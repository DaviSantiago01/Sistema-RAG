import os

# Diretório base (Legal_AI/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminhos
DOCS_DIR = os.path.join(BASE_DIR, "data", "documentos")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# Criar se não existir
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)