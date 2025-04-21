# Arquivo app/routers/documents.py

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from typing import Optional

from backend.app.schemas.transcription import UploadResponse
from backend.app.services.rag_service import RAGService, get_rag_service

# Configuração básica do logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de documento clínico",
    description="Recebe um arquivo de texto contendo informações sobre síndromes vasculares e localizações neurológicas."
)
async def upload_clinical_document(
    file: UploadFile = File(..., description="Arquivo de texto (.txt) com informações clínicas."),
    source: Optional[str] = Form(None, description="Fonte do documento (ex: literatura, artigo científico)."),
    rag_service: RAGService = Depends(get_rag_service) # Injeção de dependência
) -> UploadResponse:
    """
    Endpoint para fazer upload de documentos clínicos para o sistema LouiS Stroke.

    - **file**: Arquivo .txt enviado pelo cliente.
    - **source**: Metadado opcional sobre a origem do documento.
    - **rag_service**: Instância do serviço RAG injetada.

    Processa o arquivo, divide em chunks, gera embeddings e armazena no banco de vetores.
    """
    logger.info(f"Recebido upload de documento clínico: {file.filename}, Content-Type: {file.content_type}, Fonte: {source}")

    # Validação básica do tipo de arquivo
    if file.content_type != "text/plain":
        logger.warning(f"Tipo de arquivo inválido recebido: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo inválido. Apenas arquivos .txt são aceitos."
        )

    try:
        # Lê o conteúdo do arquivo de forma assíncrona
        content_bytes = await file.read()
        content_text = content_bytes.decode("utf-8")
        logger.debug(f"Arquivo '{file.filename}' lido com sucesso ({len(content_bytes)} bytes).")

        if not content_text.strip():
            logger.warning(f"Arquivo '{file.filename}' está vazio ou contém apenas espaços em branco.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O documento clínico não pode estar vazio."
            )

        # Chama o serviço RAG para processar e armazenar o documento clínico
        document_id = file.filename or f"doc_{source or 'unknown'}" # Usa nome do arquivo ou source como ID base
        num_chunks_added = await rag_service.process_and_store_clinical_text(
            text=content_text,
            document_id=document_id,
            metadata={"source": source or "Não especificada", "filename": file.filename}
        )

        logger.info(f"Documento clínico '{document_id}' processado e armazenado com sucesso ({num_chunks_added} chunks).")
        return UploadResponse(
            message="Documento clínico processado e armazenado com sucesso!",
            document_id=document_id, # Retorna um ID representativo
            chunks_added=num_chunks_added
        )

    except ValueError as ve:
        logger.error(f"Erro de valor durante o processamento de '{file.filename}': {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar o documento: {ve}"
        )
    except Exception as e:
        logger.exception(f"Erro inesperado durante o upload/processamento de '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno ao processar o documento: {e}"
        )
    finally:
        # Garante que o arquivo seja fechado mesmo se ocorrerem erros
        await file.close()
        logger.debug(f"Arquivo '{file.filename}' fechado.")