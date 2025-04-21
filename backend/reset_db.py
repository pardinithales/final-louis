# reset_db.py
import shutil
import os
import logging
from pathlib import Path
from backend.app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_chroma_db():
    # Obter caminho do diretório de persistência
    db_path = Path(settings.CHROMA_PERSIST_DIRECTORY)
    
    logger.info(f"Removendo diretório Chroma DB: {db_path}")
    
    # Verificar se o diretório existe
    if db_path.exists():
        # Excluir o diretório inteiro
        shutil.rmtree(db_path)
        logger.info("Diretório removido com sucesso!")
    else:
        logger.info("Diretório não encontrado, nada para excluir.")
    
    # Criar diretório vazio novamente
    os.makedirs(db_path, exist_ok=True)
    logger.info(f"Diretório vazio recriado: {db_path}")
    logger.info("Banco de dados reinicializado com sucesso!")

if __name__ == "__main__":
    reset_chroma_db()