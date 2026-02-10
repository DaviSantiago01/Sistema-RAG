import streamlit as st
from frontend.state import inicializar_estado_sessao
from frontend.ui import renderizar_login_registro, renderizar_barra_lateral, renderizar_chat, api

# Configuração da Página
st.set_page_config(page_title="Projeto RAG", page_icon="🧠", layout="wide")

# Inicialização do Estado
inicializar_estado_sessao()

# Fluxo Principal
if not st.session_state.token:
    renderizar_login_registro()
else:
    # Se o usuário tem token mas não tem nome (ex: reload de página), busca info
    if not st.session_state.user_name:
        try:
            user = api.obter_info_usuario()
            st.session_state.user_name = user.get("nome") or user.get("email")
        except:
            st.session_state.user_name = "Usuário"
            
    renderizar_barra_lateral()
    renderizar_chat()
