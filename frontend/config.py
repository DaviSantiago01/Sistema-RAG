import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
TIMEOUT = 300

class Rotas:
    LOGIN = "/token"
    REGISTER = "/register"
    CARREGAR = "/carregar/"
    PROCESSAR = "/processar"
    PERGUNTA = "/pergunta/"
    DOCUMENTOS = "/documentos/"
    CONVERSAS = "/conversas/"
    ME = "/users/me"
