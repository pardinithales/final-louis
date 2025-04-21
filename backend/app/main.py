# Arquivo app/main.py
#
# Este é o ponto de entrada principal da aplicação: 
# - Inicializa o servidor FastAPI
# - Configura rotas e middlewares
# - Estabelece eventos de inicialização

# Hack para sqlite3 (necessário apenas em Linux/Deploy)
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import logging
from contextlib import asynccontextmanager
import os # Adicionado import os
import shutil
import glob
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Adicionado import

from backend.app.core.config import settings
from backend.app.routers import api_router
from backend.app.services.vector_store import get_vector_store_service
from backend.image_selector import get_available_images, clear_available_images_cache

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

# Obtém o caminho para o diretório de imagens original
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SOURCE_IMAGES_DIR = os.path.join(BASE_DIR, "images")
# -----------------------------------------

# Função para sincronizar as imagens da pasta raiz/images para static/images
def sync_images():
    """
    Sincroniza as imagens da pasta original (projeto raiz/images) para a pasta static/images
    usada pelo FastAPI para servir arquivos estáticos.
    """
    try:
        # Log do path absoluto para verificação
        abs_source_dir = os.path.abspath(SOURCE_IMAGES_DIR)
        abs_dest_dir = os.path.abspath(IMAGES_DIR)
        logger.info(f"Diretório de origem (abs): {abs_source_dir}")
        logger.info(f"Diretório de destino (abs): {abs_dest_dir}")
        
        # Verificar se o diretório de origem existe
        if not os.path.exists(SOURCE_IMAGES_DIR):
            logger.warning(f"Diretório de imagens de origem não encontrado: {SOURCE_IMAGES_DIR}")
            return
            
        # Limpar o diretório de destino para evitar arquivos obsoletos
        for old_file in glob.glob(os.path.join(IMAGES_DIR, "*.png")):
            os.remove(old_file)
            
        # Copiar todas as imagens da pasta original para a pasta static/images
        image_files = glob.glob(os.path.join(SOURCE_IMAGES_DIR, "*.png"))
        logger.info(f"Encontradas {len(image_files)} imagens para sincronizar")
        
        for image_file in image_files:
            filename = os.path.basename(image_file)
            dest_path = os.path.join(IMAGES_DIR, filename)
            shutil.copy2(image_file, dest_path)
            
        logger.info(f"Sincronizadas {len(image_files)} imagens para {IMAGES_DIR}")
        
        # Verificar se os arquivos foram copiados corretamente
        copied_files = glob.glob(os.path.join(IMAGES_DIR, "*.png"))
        logger.info(f"Verificação: {len(copied_files)} imagens presentes no diretório de destino")
        
        # Limpar o cache de imagens para forçar uma nova busca com os arquivos atualizados
        clear_available_images_cache()
        
        # Pré-carregar a lista de imagens para garantir que estejam disponíveis
        images = get_available_images()
        logger.info(f"Lista de imagens pré-carregada: {len(images)} imagens disponíveis")
        if len(images) == 0:
            logger.warning("ALERTA: Nenhuma imagem foi carregada após a sincronização")
            for path in [SOURCE_IMAGES_DIR, IMAGES_DIR]:
                if os.path.exists(path):
                    files = os.listdir(path)
                    logger.info(f"Arquivos em {path}: {len(files)} ({', '.join(files[:5])}{'...' if len(files) > 5 else ''})")
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar imagens: {e}")
        logger.exception("Detalhes do erro:")


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
        # Sincronizar imagens da pasta original para a pasta static/images
        sync_images()
        logger.info("Imagens sincronizadas com sucesso.")
        
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
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # Permite todas as origens (ajuste em produção!)
#     allow_credentials=True,
#     # Métodos HTTP permitidos (todos)
#     allow_methods=["*"],
#     # Cabeçalhos permitidos nas requisições
#     allow_headers=["*"], # Permite todos os cabeçalhos
#     # Cabeçalhos expostos
#     expose_headers=["*"],
# )

@app.get("/")
async def root():
    """
    Endpoint raiz simples para verificar se a API está online.
    """
    # Mensagem atualizada para indicar a versão
    return {"message": f"Bem-vindo à API v1 {settings.APP_TITLE}!"}

# Você pode adicionar mais endpoints globais aqui, se necessário