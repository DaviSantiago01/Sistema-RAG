# Imports Gerais
import os
import threading
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, UploadFile, HTTPException
from .config import DOCS_DIR, CHROMA_DIR
from contextlib import asynccontextmanager

# Import backends
from sqlalchemy.orm import Session
from .database import get_db, create_tables
from .models import Documento, Conversa, Mensagem
from .schemas import DocumentoResponse, QueryRequest, QueryResponse

# Configuração
in_docker = os.path.exists("/.dockerenv")
load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", ".env"),
    encoding="utf-8",
    override=not in_docker,
)

# Inicialização tardia (evita bloquear o bind da porta 8000 no import)
llm = None
embeddings = None
_models_lock = threading.Lock()

_db_lock = threading.Lock()
_db_initialized = False


def _inicializar_modelos():
    # Lazy import: evita travar o startup só por importar torch/langchain
    from langchain_groq import ChatGroq
    from langchain_community.embeddings import HuggingFaceEmbeddings

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não encontrado nas variáveis de ambiente.")

    local_llm = ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0
    )


    local_embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    return local_llm, local_embeddings


def _obter_modelos():
    global llm, embeddings
    if llm is not None and embeddings is not None:
        return llm, embeddings

    with _models_lock:
        if llm is None or embeddings is None:
                llm, embeddings = _inicializar_modelos()
    return llm, embeddings


def _garantir_db():
    global _db_initialized
    if _db_initialized:
        return
    with _db_lock:
        if _db_initialized:
            return
        create_tables()
        _db_initialized = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Legal AI RAG", lifespan=lifespan)


# API: Upload de PDF
@app.post("/carregar/", response_model=DocumentoResponse)
async def carregar_documentos(file: UploadFile, db: Session = Depends(get_db)):
    """Recebe e salva PDF no servidor"""
    _garantir_db()
    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas PDFs são permitidos.")
    
    # Verifica o tamanho do arquivo PDF antes de salvar (move o ponteiro para o final, lê o tamanho em bytes, e retorna ao início)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 10MB)")

    # Verifique se o diretório existe, se não, cria
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Caminho para salvar o arquivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo inválido.")
    caminho_arquivo = os.path.join(DOCS_DIR, file.filename)

    try:
        # Salva o arquivo PDF enviado pelo usuário
        # Abre o arquivo para escrita binária ('wb') — necessário para salvar PDFs e outros arquivos não-texto sem corromper os dados
        with open(caminho_arquivo, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")

    documento_existente = db.query(Documento).filter(Documento.nome_arquivo == file.filename).first()
    if documento_existente:
        documento_existente.nome_original = file.filename
        documento_existente.caminho_arquivo = caminho_arquivo
        db.commit()
        db.refresh(documento_existente)
        return documento_existente

    doc = Documento(
        nome_arquivo=file.filename,
        nome_original=file.filename,
        caminho_arquivo=caminho_arquivo
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc

# API: Processar e indexar PDF
@app.post("/processar/{filename}")
async def processar_documento(filename: str, db: Session = Depends(get_db)):
    """Carrega PDF, faz chunking e salva no vector store"""
    _garantir_db()
    _, local_embeddings = _obter_modelos()

    # Lazy import
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma

    caminho_arquivo = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    try:
        # Carregar PDF
        loader = PyPDFLoader(caminho_arquivo)
        documento = loader.load()

        # Dividir em chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documento)

        # Salvar no ChromaDB
        vectordb = Chroma.from_documents(
            chunks,
            embedding=local_embeddings,
            persist_directory=CHROMA_DIR
        )

        documento_db = db.query(Documento).filter(Documento.nome_arquivo == filename).first()
        if documento_db:
            db.query(Documento).filter(Documento.nome_arquivo == filename).update({
                "preprocessado": True,
                "numero_chuncks": len(chunks)
            })
            db.commit()

        return {
            "message": "Documento processado e armazenado com sucesso.",
            "filename": filename,
            "num_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

# API: Fazer pergunta ao RAG
@app.post("/pergunta/", response_model=QueryResponse)
async def responder_pergunta(query: QueryRequest, db: Session = Depends(get_db)):
    """Busca documentos relevantes e gera resposta com LLM"""
    _garantir_db()
    local_llm, local_embeddings = _obter_modelos()
    try:
        # Lazy import
        from langchain_community.vectorstores import Chroma
        from langchain_core.messages import HumanMessage, SystemMessage

        # Carregar vector store
        vectordb = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=local_embeddings
        )

        # Validar se há documentos na base
        count = vectordb._collection.count()
        if count == 0:
            raise HTTPException(status_code=404, detail="Nenhum documento indexado. Por favor, processe um documento primeiro.")
        
        # Buscar documentos similares
        docs = vectordb.similarity_search(query.pergunta, k=3)

        # Montar contexto
        context_parts = []
        for doc in docs:
            fonte = doc.metadata.get('source', 'N/A')
            context_parts.append(f"Fonte: {fonte}\n{doc.page_content}")
        context = "\n\n---\n\n".join(context_parts)

        # Criar prompt
        messages = [
            SystemMessage(content="Você é um assistente jurídico que responde com base APENAS no contexto fornecido. Cite as fontes."),
            HumanMessage(content=f"Contexto:\n{context}\n\nPergunta: {query.pergunta}")
        ]

        # Gerar resposta
        resposta = local_llm.invoke(messages)

        conversa = Conversa(titulo=query.pergunta[:50])
        db.add(conversa)
        db.commit()

        msg_user = Mensagem(
            conversa_id=conversa.id,
            conteudo=query.pergunta,
            remetente="user"
        )
        msg_ia = Mensagem(
            conversa_id=conversa.id,
            conteudo=resposta.content,
            remetente="ia"
        )
        db.add(msg_user)
        db.add(msg_ia)
        db.commit()

        return {
            "resposta": resposta.content,
            "sources": [doc.metadata for doc in docs],
            "num_docs": len(docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
    
@app.get("/documentos/")
async def listar_documentos():
    """Lista os documentos carregados no servidor"""
    try:
        # Verifica o diretório de documentos, se nao existir, retorna lista vazia
        if not os.path.exists(DOCS_DIR):
            return {
                "documentos": [],
                "total": 0
            }

        # Lista os arquivos PDF no diretório, list comprehension para filtrar apenas PDFs
        documentos = [f for f in os.listdir(DOCS_DIR) if f.endswith('.pdf')] 

        return {
            "documentos": documentos,
            "total": len(documentos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro {str(e)}")
