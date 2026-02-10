# Docker

## Visão geral
A aplicação é empacotada em uma única imagem base e orquestrada via Docker Compose com três serviços: PostgreSQL, backend e frontend.

## Dockerfile
- Base: `ghcr.io/astral-sh/uv:python3.11-bookworm-slim`.
- Instala dependências do sistema para o PostgreSQL (`libpq-dev`) e build.
- Usa `uv` para instalar dependências Python.
- Copia backend, frontend, dados e `app.py`.
- Expõe portas 8000 (API) e 8501 (Streamlit).

## docker-compose.yml
- `postgres`: container de banco com volume `postgres_data`.
- `backend`: executa `uvicorn` e monta volumes de código, dados e Chroma.
- `frontend`: executa `streamlit` e monta código do frontend.
- Variáveis de ambiente centralizadas em `.env`.

## Volumes
- `postgres_data`: persistência do banco relacional.
- `./chroma_db`: persistência do banco vetorial.
- `./data`: persistência de documentos.

## Portas
- `5433:5432` para PostgreSQL.
- `8000:8000` para API.
- `8501:8501` para frontend.

