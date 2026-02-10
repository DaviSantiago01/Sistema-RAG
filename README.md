# 🧠 Projeto RAG — Assistente de Documentos

Sistema RAG para análise e perguntas sobre documentos em PDF.

---

## ✅ O que este projeto faz

- Upload de PDFs
- Indexação em vetores (Chroma)
- Perguntas com RAG + LLM
- Respostas com fontes

---

## 🧱 Arquitetura (visão rápida)

```
PDFs → Text Splitter → Embeddings → ChromaDB
                                         ↓
Pergunta → Busca Vetorial → RAG → LLM → Resposta + Fonte
```

---

## 🧰 Stack

- Backend: FastAPI + LangChain
- Vetores: ChromaDB
- LLM: Groq
- Embeddings: Google
- Frontend: Streamlit
- Banco: PostgreSQL

---

## ⚙️ Variáveis de ambiente

Crie um .env baseado em [.env.example](.env.example) e preencha:

- `GROQ_API_KEY` (obrigatório)
- `GOOGLE_API_KEY` (obrigatório)
- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`

---

## ▶️ Como rodar localmente (dev)

1. Instale dependências

```
pip install -r requirements.txt
```

2. Inicie o backend

```
uvicorn backend.main:app --reload
```

3. Inicie o frontend

```
streamlit run app.py
```

---

## 🔌 Endpoints principais

- `POST /carregar/` — upload de PDF
- `POST /processar/{filename}` — indexar documento
- `POST /pergunta/` — perguntar ao RAG
- `GET /documentos/` — listar PDFs

---

## 📁 Estrutura principal

- API: [backend/main.py](backend/main.py)
- Frontend: [app.py](app.py)
- Dependências: [requirements.txt](requirements.txt)

---

## ⚠️ Observações

- Não versionar `.env` (já ignorado em [.gitignore](.gitignore))
- PDFs ficam em `data/documentos` (ignorado do git)

---
