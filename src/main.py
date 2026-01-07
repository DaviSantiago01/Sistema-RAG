# Imports Gerais
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException

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
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 10MB)")

    
    os.makedirs("data/documents/", exist_ok=True)
    caminho_arquivo = f"data/documents/{file.filename}"

    try:
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
    caminho_arquivo = f"data/documents/{filename}"
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
            persist_directory="./chroma_db"
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
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )
        
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