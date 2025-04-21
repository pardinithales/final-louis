# Arquivo app/main.py
#
# Este é o ponto de entrada principal da aplicação: 
# - Inicializa o servidor FastAPI
# - Configura rotas e middlewares
# - Estabelece eventos de inicialização

# Hack para sqlite3 ANTES de qualquer importação que possa usar chromadb
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import logging
from contextlib import asynccontextmanager
import os # Adicionado import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Adicionado import

from backend.app.core.config import settings
from backend.app.routers import api_router
from backend.app.services.vector_store import get_vector_store_service

# Configuração básica do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração de Arquivos Estáticos ---
# Define o diretório base para arquivos estáticos
STATIC_DIR = "static"
# Define o subdiretório para imagens dentro do diretório estático
IMAGES_DIR = os.path.join(STATIC_DIR, "images")
# Garante que o diretório de imagens exista ao iniciar a aplicação
os.makedirs(IMAGES_DIR, exist_ok=True)
# -----------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida do aplicativo usando o novo gerenciador de contexto assíncrono.
    """
    # Código a ser executado ANTES da aplicação começar a receber requests (startup)
    logger.info("Iniciando LouiS Stroke API...")
    logger.info(f"Usando ChromaDB em: {settings.CHROMA_PERSIST_DIRECTORY}")
    logger.info(f"Nome da coleção ChromaDB: {settings.CHROMA_COLLECTION_NAME}")
    logger.info(f"Modelo de embedding: {settings.EMBEDDING_MODEL_NAME}")
    
    try:
        # Inicializar ChromaDB e serviços relacionados
        vector_store_service = get_vector_store_service()
        logger.info("Vector Store inicializado com sucesso.")
    except Exception as e:
        logger.critical(f"Falha na inicialização da aplicação: {e}", exc_info=True)
        raise e

    yield # A aplicação roda aqui
    
    # Código a ser executado APÓS a aplicação parar de receber requests (shutdown)
    logger.info("Encerrando LouiS Stroke API...")


# Criação da aplicação FastAPI com o gerenciador de ciclo de vida
app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_TITLE, # Usando título do config
    description="API especializada em localização neurológica de AVC usando RAG.",
    version="1.0.0",
)

# --- Montar Arquivos Estáticos ---
# Serve arquivos da pasta 'static' sob o caminho '/static' na URL
# Ex: Uma imagem em static/images/img.png será acessível em http://.../static/images/img.png
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# -------------------------------


# Inclusão do roteador da API com prefixo /api/v1
# Todas as rotas definidas em api_router (query, image, etc.) terão /api/v1 na frente
app.include_router(api_router, prefix="/api/v1")

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite todas as origens (ajuste em produção!)
    allow_credentials=True,
    # Métodos HTTP permitidos
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # Cabeçalhos permitidos nas requisições
    allow_headers=["*"], # Permite todos os cabeçalhos (ajuste se necessário)
)

@app.get("/")
async def root():
    """
    Endpoint raiz simples para verificar se a API está online.
    """
    # Mensagem atualizada para indicar a versão
    return {"message": f"Bem-vindo à API v1 {settings.APP_TITLE}!"}

# Você pode adicionar mais endpoints globais aqui, se necessário