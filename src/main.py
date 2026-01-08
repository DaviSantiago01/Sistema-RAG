# Imports Gerais
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from config import DOCS_DIR, CHROMA_DIR

# LangChain - Loaders, Splitters, Embeddings, Vector Stores, LLMs e Messages
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


# Configuração
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY não encontrado nas variáveis de ambiente.")

app = FastAPI(title="Legal AI RAG")

# Inicialização global de LLM e Embeddings
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# API: Upload de PDF
@app.post("/carregar/")
async def carregar_documentos(file: UploadFile = File(...)):
    """Recebe e salva PDF no servidor"""
    if not file.filename.endswith('.pdf'):
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
    caminho_arquivo = os.path.join(DOCS_DIR, file.filename)

    try:
        # Salva o arquivo PDF enviado pelo usuário
        # Abre o arquivo para escrita binária ('wb') — necessário para salvar PDFs e outros arquivos não-texto sem corromper os dados
        with open(caminho_arquivo, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")

    return {
        "message": "Arquivo carregado com sucesso.",
        "filename": file.filename,
        "path": caminho_arquivo
    }

# API: Processar e indexar PDF
@app.post("/processar/{filename}")
async def processar_documento(filename: str):
    """Carrega PDF, faz chunking e salva no vector store"""
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
            embedding=embeddings,
            persist_directory=CHROMA_DIR
        )

        return {
            "message": "Documento processado e armazenado com sucesso.",
            "filename": filename,
            "num_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

# API: Fazer pergunta ao RAG
@app.post("/pergunta/")
async def responder_pergunta(pergunta: str):
    """Busca documentos relevantes e gera resposta com LLM"""
    try:
        # Carregar vector store
        vectordb = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )

        # Validar se há documentos na base
        count = vectordb._collection.count()
        if count == 0:
            raise HTTPException(status_code=404, detail="Nenhum documento indexado. Por favor, processe um documento primeiro.")
        
        # Buscar documentos similares
        docs = vectordb.similarity_search(pergunta, k=3)

        # Montar contexto
        context_parts = []
        for doc in docs:
            fonte = doc.metadata.get('source', 'N/A')
            context_parts.append(f"Fonte: {fonte}\n{doc.page_content}")
        context = "\n\n---\n\n".join(context_parts)

        # Criar prompt
        messages = [
            SystemMessage(content="Você é um assistente jurídico que responde com base APENAS no contexto fornecido. Cite as fontes."),
            HumanMessage(content=f"Contexto:\n{context}\n\nPergunta: {pergunta}")
        ]

        # Gerar resposta
        resposta = llm.invoke(messages)

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
