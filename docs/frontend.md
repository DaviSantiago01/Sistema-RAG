# Frontend

## Visão geral
O frontend é um aplicativo Streamlit que consome a API do backend via HTTP. Ele organiza autenticação, upload de documentos, indexação e chat com o RAG.

## Estrutura de arquivos
- `app.py`: ponto de entrada do Streamlit e fluxo principal da UI.
- `frontend/ui.py`: componentes de interface e handlers de interação.
- `frontend/api.py`: cliente HTTP com sessão e tratamento de respostas.
- `frontend/state.py`: estado de sessão e reset do usuário.
- `frontend/config.py`: URL do backend e rotas.

## Fluxos principais
1. Login e cadastro com JWT.
2. Upload de PDF e indexação do documento.
3. Consulta ao RAG e exibição das respostas.
4. Listagem de documentos e conversas.

## Integração com backend
- O cliente `ClienteAPI` centraliza requisições e injeta `Authorization: Bearer <token>`.
- A URL do backend é configurada por `BACKEND_URL`.

## Tecnologias
- Streamlit, Requests.

