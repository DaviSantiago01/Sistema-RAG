import requests
import streamlit as st
from typing import Optional, Dict, Any, Tuple
from .config import BACKEND_URL, TIMEOUT, Rotas

class ClienteAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = BACKEND_URL

    def _obter_cabecalhos(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        auth_token = token if token else st.session_state.get("token")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _tratar_resposta(self, response: requests.Response) -> Any:
        if not response.ok:
            if response.status_code == 401:
                # Token expirado ou inválido
                return {"error": "Unauthorized", "status": 401}
            
            try:
                detail = response.json().get("detail", "")
            except:
                detail = response.text
            
            error_msg = (detail or "").strip()
            if len(error_msg) > 300:
                error_msg = error_msg[:300] + "..."
            
            raise Exception(error_msg or f"Erro HTTP {response.status_code}")
        
        return response.json()

    def requisitar(self, metodo: str, endpoint: str, token: Optional[str] = None, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        headers = self._obter_cabecalhos(token)
        # Mesclar headers se fornecidos em kwargs
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        try:
            response = self.session.request(
                method=metodo, 
                url=url, 
                headers=headers, 
                timeout=TIMEOUT, 
                **kwargs
            )
            return self._tratar_resposta(response)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Falha de conexão com o backend: {str(e)}")

    def login(self, username, password) -> Tuple[Optional[str], Optional[str]]:
        try:
            data = self.requisitar("POST", Rotas.LOGIN, data={"username": username, "password": password})
            # Lidar com retorno potencial 401 de _tratar_resposta se não foi levantado
            if isinstance(data, dict) and data.get("status") == 401:
                 return None, "Credenciais inválidas"
            return data["access_token"], None
        except Exception as e:
            return None, str(e)

    def registrar(self, email, password, nome) -> Tuple[bool, Any]:
        try:
            res = self.requisitar("POST", Rotas.REGISTER, json={"email": email, "password": password, "nome": nome})
            if isinstance(res, dict) and res.get("status") == 401:
                return False, "Erro de autorização"
            return True, res
        except Exception as e:
            return False, str(e)

    def obter_info_usuario(self):
        return self.requisitar("GET", Rotas.ME)

    def obter_documentos(self, token):
        return self.requisitar("GET", Rotas.DOCUMENTOS, token=token)

    def obter_conversas(self, token):
        return self.requisitar("GET", Rotas.CONVERSAS, token=token)

    def obter_mensagens(self, conversa_id):
        return self.requisitar("GET", f"/conversas/{conversa_id}/mensagens/")

    def enviar_documento(self, files):
        return self.requisitar("POST", Rotas.CARREGAR, files=files)

    def processar_documento(self, nome_arquivo):
        return self.requisitar("POST", f"{Rotas.PROCESSAR}/{nome_arquivo}")

    def fazer_pergunta(self, payload):
        return self.requisitar("POST", Rotas.PERGUNTA, json=payload)

api = ClienteAPI()
