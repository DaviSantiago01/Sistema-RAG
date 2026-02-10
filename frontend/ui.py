import streamlit as st
from urllib.parse import quote
from .api import api
from .state import resetar_estado_sessao

def renderizar_login_registro():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Acesso ao Sistema RAG")
        tab1, tab2 = st.tabs(["Login", "Criar Conta"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                senha = st.text_input("Senha", type="password")
                submit_login = st.form_submit_button("Entrar", type="primary")

            if submit_login:
                token, erro = api.login(email, senha)
                if token:
                    st.session_state.token = token
                    try:
                        user = api.obter_info_usuario()
                        st.session_state.user_name = user.get("nome") or user.get("email")
                    except:
                        st.session_state.user_name = "Usuário"
                    st.success("Login realizado!")
                    st.rerun()
                else:
                    st.error(f"Erro no login: {erro}")

        with tab2:
            with st.form("register_form"):
                new_email = st.text_input("Email para cadastro")
                new_nome = st.text_input("Seu Nome")
                new_senha = st.text_input("Crie uma Senha", type="password")
                submit_register = st.form_submit_button("Cadastrar")

            if submit_register:
                if not new_senha:
                    st.error("Senha é obrigatória")
                else:
                    ok, res = api.registrar(new_email, new_senha, new_nome)
                    if ok:
                        st.success("Conta criada! Faça login agora.")
                    else:
                        st.error(f"Erro ao criar conta: {res}")

@st.cache_data(ttl=30)
def obter_documentos_cache(token):
    return api.obter_documentos(token)

@st.cache_data(ttl=30)
def obter_conversas_cache(token):
    return api.obter_conversas(token)

def renderizar_barra_lateral():
    with st.sidebar:
        st.title("📄 Painel")
        st.write(f"Logado como: **{st.session_state.user_name}**")
        if st.button("Sair"):
            resetar_estado_sessao()
            st.rerun()
        
        st.markdown("---")
        st.header("Upload e Indexação")
        
        with st.expander("📂 Meus Documentos", expanded=False):
            try:
                docs = obter_documentos_cache(st.session_state.token)
                if docs.get("total", 0) > 0:
                    for d in docs["documentos"]:
                        st.text(f"📄 {d}")
                else:
                    st.caption("Nenhum documento.")
            except Exception:
                st.caption("Erro ao listar.")

        arquivo_pdf = st.file_uploader("Selecione PDF", type=["pdf"])
        
        col1, col2 = st.columns(2)
        if col1.button("Enviar"):
            if arquivo_pdf:
                try:
                    files = {"file": (arquivo_pdf.name, arquivo_pdf.getvalue(), "application/pdf")}
                    res = api.enviar_documento(files)
                    st.session_state.nome_arquivo = res["nome_arquivo"]
                    st.session_state.documento_indexado = False
                    st.success("Enviado!")
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        if col2.button("Indexar"):
            if st.session_state.nome_arquivo:
                try:
                    nome = quote(st.session_state.nome_arquivo)
                    api.processar_documento(nome)
                    st.session_state.documento_indexado = True
                    st.success("Indexado!")
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.markdown("---")
        st.header("🗃️ Histórico de Conversas")
        if st.button("+ Nova Conversa"):
            st.session_state.mensagens = []
            st.session_state.conversa_atual_id = None
            st.rerun()

        try:
            conversas = obter_conversas_cache(st.session_state.token)
            for conv in conversas:
                label = f"{conv['titulo']} ({conv['criado_em'][:10]})"
                if st.button(label, key=conv["id"]):
                    carregar_historico_chat(conv["id"])
        except Exception:
            st.caption("Sem histórico ou erro ao carregar.")

def carregar_historico_chat(conversa_id):
    try:
        msgs = api.obter_mensagens(conversa_id)
        historico_formatado = []
        for m in msgs:
            papel = "user" if m["remetente"] == "user" else "assistant"
            historico_formatado.append({"papel": papel, "texto": m["conteudo"]})
        st.session_state.mensagens = historico_formatado
        st.session_state.conversa_atual_id = conversa_id
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")

def renderizar_chat():
    st.title("🧠 Assistente Inteligente (RAG)")

    if not st.session_state.mensagens:
        st.info("Comece uma nova conversa ou selecione uma antiga no menu.")

    for msg in st.session_state.mensagens:
        with st.chat_message(msg["papel"]):
            st.markdown(msg["texto"])

    pergunta = st.chat_input("Digite sua pergunta...")
    if pergunta:
        st.session_state.mensagens.append({"papel": "user", "texto": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("⏳ Pensando...")
            try:
                payload = {"pergunta": pergunta}
                if st.session_state.conversa_atual_id:
                    payload["conversa_id"] = st.session_state.conversa_atual_id
                    
                res = api.fazer_pergunta(payload)
                resposta = res["resposta"]
                placeholder.markdown(resposta)
                st.session_state.mensagens.append({"papel": "assistant", "texto": resposta})
                
                # Atualizar ID da conversa se for nova
                if not st.session_state.conversa_atual_id:
                    conversa_id = res.get("conversa_id")
                    if conversa_id:
                        st.session_state.conversa_atual_id = conversa_id
                        st.rerun()
                    
            except Exception as e:
                placeholder.error(f"Erro: {e}")
