# Arquivo app/core/config.py

import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pydantic import Field

# Configuração básica do logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Configurações globais da aplicação.
    """

    # Configuração da OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")

    # Configuração do ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "../chroma_db_louis"  # Ajuste para o caminho relativo
    CHROMA_COLLECTION_NAME: str = "stroke_syndromes"

    # Configuração do embedding
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Configurações do chunking
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200
    DEFAULT_TOP_K: int = 5

    # Front-end config
    APP_TITLE: str = "LouiS Stroke - Neurological Localization System"
    WELCOME_MESSAGE: str = (
        "Welcome to LouiS Stroke, the leading expert system for "
        "neurological localization in stroke patients."
    )

    # Configuração para carregar variáveis de um arquivo .env
    model_config = SettingsConfigDict(
        env_file='../.env',
        env_file_encoding='utf-8',
        extra='ignore' # Ignora variáveis extras no .env que não estão definidas aqui
    )

# Instancia única das configurações para ser importada em outros módulos
try:
    # Remove qualquer instância anterior para garantir recarregamento
    if 'settings' in globals():
        del globals()['settings']
    
    settings = Settings()
    # Log das configurações carregadas (exceto segredos)
    logger.info("Configurações carregadas:")
    logger.info(f"  CHROMA_PERSIST_DIRECTORY: {settings.CHROMA_PERSIST_DIRECTORY}")
    logger.info(f"  CHROMA_COLLECTION_NAME: {settings.CHROMA_COLLECTION_NAME}")
    logger.info(f"  EMBEDDING_MODEL_NAME: {settings.EMBEDDING_MODEL_NAME}")
    logger.info(f"  CHUNK_SIZE: {settings.CHUNK_SIZE}")
    logger.info(f"  CHUNK_OVERLAP: {settings.CHUNK_OVERLAP}")
    logger.info(f"  DEFAULT_TOP_K: {settings.DEFAULT_TOP_K}")
    logger.info(f"  APP_TITLE: {settings.APP_TITLE}")
    logger.info(f"  WELCOME_MESSAGE: {settings.WELCOME_MESSAGE}")

    # Garante que o diretório do ChromaDB exista
    os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    logger.debug(f"Diretório ChromaDB '{settings.CHROMA_PERSIST_DIRECTORY}' verificado/criado.")

except Exception as e:
    logger.exception("Erro ao carregar as configurações!")
    # Em um cenário real, pode ser preferível lançar o erro para interromper a inicialização
    raise RuntimeError("Falha ao carregar configurações essenciais.") from e