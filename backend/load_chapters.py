"""
Script para carregar documentos da pasta 'chapters' no sistema LouiS Stroke.
"""
# Adiciona o hack para sqlite3 antes de qualquer outra importação que possa usar chromadb
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import asyncio
import logging
import glob
from backend.app.services.rag_service import get_rag_service
from backend.app.services.vector_store import get_vector_store_service

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho para a pasta chapters (relativo à raiz do projeto)
CHAPTERS_DIR = "chapters"

async def load_chapters_data():
    """Carrega os arquivos da pasta chapters no sistema."""
    # Inicializar serviços
    logger.info("Inicializando serviços...")
    vector_store = get_vector_store_service()
    rag_service = get_rag_service(vector_store=vector_store)
    
    # Verifica se já existem documentos
    count = vector_store.count_documents()
    logger.info(f"Total de documentos na coleção: {count}")
    
    if count > 0:
        logger.info("A coleção já contém documentos. Deseja limpar e recarregar? (S/N)")
        response = input().strip().upper()
        if response == "S":
            # Limpar coleção (use com cuidado)
            logger.warning("Limpando coleção...")
            vector_store.delete_documents(where={})
            logger.info("Coleção limpa.")
        else:
            logger.info("Operação cancelada.")
            return
    
    # Listar arquivos na pasta chapters
    chapter_files = glob.glob(f"{CHAPTERS_DIR}/*.txt")
    logger.info(f"Encontrados {len(chapter_files)} arquivos na pasta {CHAPTERS_DIR}")
    
    if not chapter_files:
        logger.error(f"Nenhum arquivo .txt encontrado na pasta {CHAPTERS_DIR}")
        return
    
    # Carregar dados
    logger.info("Carregando documentos da pasta chapters...")
    total_chunks = 0
    
    for file_path in sorted(chapter_files):
        filename = os.path.basename(file_path)
        # Usar o número do capítulo e o nome como ID
        document_id = filename.split('_extracted')[0].strip()
        
        logger.info(f"Processando arquivo '{filename}'...")
        
        try:
            # Ler conteúdo do arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Arquivo '{filename}' está vazio. Pulando...")
                continue
            
            # Processar e armazenar o texto
            chunks_added = await rag_service.process_and_store_clinical_text(
                text=content,
                document_id=document_id,
                metadata={
                    "source": "chapters",
                    "filename": filename,
                    "type": "stroke_syndrome"
                }
            )
            
            logger.info(f"Arquivo '{filename}' processado ({chunks_added} chunks).")
            total_chunks += chunks_added
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo '{filename}': {e}")
    
    # Verificar total de documentos após carregamento
    count = vector_store.count_documents()
    logger.info(f"Total de documentos na coleção após carregamento: {count}")
    logger.info(f"Total de chunks adicionados: {total_chunks}")
    logger.info("Carregamento de chapters concluído!")

if __name__ == "__main__":
    asyncio.run(load_chapters_data()) 