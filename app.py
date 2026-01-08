import streamlit as st
import requests

st.set_page_config(page_title="Legal AI", page_icon="⚖️")

st.title("⚖️ Legal AI - Sistema RAG Jurídico")
st.markdown("---")

# Upload de PDF
st.subheader("📄 Upload de Documentos")
uploaded_file = st.file_uploader("Escolha um PDF", type="pdf")

if uploaded_file and st.button("📤 Enviar Documento"):
    with st.spinner("Fazendo upload..."):
        try:
            files = {"file": uploaded_file}
            response = requests.post("http://localhost:8000/carregar/", files=files)
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ {data['message']}")
                st.info(f"**Arquivo:** {data['filename']}")
                st.session_state['uploaded_filename'] = data['filename']
            elif response.status_code == 400:
                st.error(f"❌ {response.json()['detail']}")
            elif response.status_code == 500:
                st.error(f"❌ {response.json()['detail']}")
            else:
                st.error(f"❌ Erro inesperado ({response.status_code})")
        except requests.exceptions.ConnectionError:
            st.error("❌ Servidor offline. Rode: uvicorn src.main:app --reload")
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

# Processar documento
if 'uploaded_filename' in st.session_state:
    st.markdown("---")
    st.subheader("⚙️ Processar Documento")
    
    filename = st.session_state['uploaded_filename']
    st.info(f"📋 Arquivo atual: **{filename}**")
    
    if st.button("🔄 Processar e Indexar"):
        with st.spinner("Processando documento..."):
            try:
                response = requests.post(f"http://localhost:8000/processar/{filename}")
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {data['message']}")
                    st.metric("Chunks criados", data['num_chunks'])
                    st.session_state['doc_processado'] = True
                else:
                    st.error(f"❌ {response.json().get('detail', 'Erro desconhecido')}")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")

# Fazer perguntas ao RAG
if st.session_state.get('doc_processado', False):
    st.markdown("---")
    st.subheader("💬 Perguntar ao Documento")
    
    pergunta = st.text_input("Faça sua pergunta:", placeholder="Ex: O que diz sobre rescisão contratual?")
    
    if st.button("🔍 Buscar Resposta"):
        if not pergunta:
            st.warning("⚠️ Digite uma pergunta primeiro!")
        else:
            with st.spinner("Buscando resposta..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/pergunta/",
                        params={"pergunta": pergunta}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Exibir resposta
                        st.success("✅ Resposta gerada!")
                        st.markdown("### 📝 Resposta:")
                        st.write(data['resposta'])
                        
                        # Exibir fontes
                        st.markdown("### 📚 Fontes utilizadas:")
                        for i, source in enumerate(data['sources'], 1):
                            st.text(f"{i}. {source.get('source', 'N/A')}")
                        
                        st.info(f"📊 Documentos consultados: {data['num_docs']}")
                        
                        # Armazenar histórico de chat
                        if "chat_history" not in st.session_state:
                            st.session_state["chat_history"] = []

                        st.session_state["chat_history"].append({
                            "pergunta": pergunta,
                            "resposta": data['resposta'],
                        })

                    else:
                        st.error(f"❌ {response.json().get('detail', 'Erro desconhecido')}")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")