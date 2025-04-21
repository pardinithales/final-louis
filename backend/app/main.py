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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.routers import api_router
from backend.app.services.vector_store import get_vector_store_service

# Configuração básica do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    title="LouiS Stroke API",
    description="API especializada em localização neurológica de AVC usando RAG.",
    version="1.0.0",
)

# Inclusão do roteador da API
app.include_router(api_router)

# Configuração do CORS para permitir chamadas de diferentes origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção é melhor especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raiz simples."""
    return {"message": "Bem-vindo à API LouiS Stroke - Especialista em Localização Neurológica!"}