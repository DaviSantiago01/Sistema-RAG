import streamlit as st

def inicializar_estado_sessao():
    defaults = {
        "token": None,
        "user_name": None,
        "mensagens": [],
        "conversa_atual_id": None,
        "nome_arquivo": "",
        "documento_indexado": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def resetar_estado_sessao():
    st.session_state.token = None
    st.session_state.user_name = None
    st.session_state.mensagens = []
    st.session_state.conversa_atual_id = None
    st.session_state.nome_arquivo = ""
    st.session_state.documento_indexado = False
