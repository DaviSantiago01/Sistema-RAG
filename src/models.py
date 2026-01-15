# src/models.py
# Definição dos modelos das tabelas do banco de dados

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# Modelo 1: Tabela de documentos
class Documento(Base):

    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, unique=True, nullable=False)
    nome_original = Column(String, nullable=False)
    caminho_arquivo = Column(String, nullable=False)
    preprocessado = Column(Boolean, default=False)
    numero_chuncks = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)

# Modelo 2: Tabela de conversas
class Conversa(Base):

    __tablename__ = "conversas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    mensagens = relationship("Mensagem", back_populates="conversa", cascade="all, delete-orphan")

# Modelo 3: Tabela de mensagens
class Mensagem(Base):

    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, index=True)
    conversa_id = Column(Integer, ForeignKey("conversas.id"), nullable=False)
    conteudo = Column(Text, nullable=False)
    remetente = Column(String, nullable=False)  
    criado_em = Column(DateTime, default=datetime.utcnow)

    conversa = relationship("Conversa", back_populates="mensagens")