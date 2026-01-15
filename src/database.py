from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
# No Windows é comum ficar com DATABASE_URL "antigo" no ambiente do sistema; fora de Docker,
# preferimos o .env. Dentro de Docker, preferimos variáveis do container.
in_docker = os.path.exists("/.dockerenv")
load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", ".env"),
    encoding="utf-8",
    override=not in_docker,
)

# Configuração do banco de dados
# Por padrão usamos a porta 5433 (mapeamento do docker-compose.yml: 5433 -> 5432).
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5433/legal_ai",
)

# Criar Engine (conexão com o banco de dados)
# Nota: Usando postgresql+psycopg:// para usar psycopg3 que corrige problemas de encoding no Windows
engine = create_engine(
    DATABASE_URL,
    echo=False
)

# Criar sessão com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos ORM
Base = declarative_base()

# Dependency - Função helper para FastAPI
def get_db():
    """
    Cria uma sessão do banco para cada requisição.
    Fecha automaticamente quando terminar.
    """
    db = SessionLocal()
    try:
        yield db  # Entrega a sessão
    finally:
        db.close()  # Fecha quando terminar

# Função para criar todas as tabelas
def create_tables():
    """
    Cria todas as tabelas definidas nos models.
    Roda apenas uma vez no início.
    """
    from .models import Documento, Conversa, Mensagem
    Base.metadata.create_all(bind=engine)