from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Esquema 1: Documento
class DocumentoCreate(BaseModel):
    nome_arquivo: str
    nome_original: str
    caminho_arquivo: str

class DocumentoResponse(BaseModel):
    id: int
    nome_arquivo: str
    nome_original: str
    caminho_arquivo: str
    preprocessado: bool
    numero_chuncks: int
    criado_em: datetime

    class Config:
        from_attributes = True

# Esquema 2: Conversa
class ConversaCreate(BaseModel):
    titulo: str

class ConversaResponse(BaseModel):
    id: int
    titulo: str
    criado_em: datetime

    class Config:
        from_attributes = True

# Esquema 3: Mensagem
class MensagemCreate(BaseModel):
    conversa_id: int
    conteudo: str
    remetente: str

class MensagemResponse(BaseModel):
    id: int
    conversa_id: int
    conteudo: str
    remetente: str
    criado_em: datetime

    class Config:
        from_attributes = True
    
# Esquema 4: Query
class QueryRequest(BaseModel):
    pergunta: str

class QueryResponse(BaseModel):
    resposta: str
    sources: list
    num_docs: int