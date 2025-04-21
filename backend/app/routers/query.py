import logging
from fastapi import APIRouter, Depends, HTTPException

from backend.app.schemas.query import QueryInput, QueryOutput
from backend.app.services.rag_service import RAGService, get_rag_service

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=QueryOutput,
    summary="Realiza uma consulta RAG",
    description="Recebe uma query de texto, recupera chunks relevantes e gera uma resposta.",
    tags=["Query"]
)
async def perform_query(
    query_input: QueryInput,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Endpoint para realizar consultas ao sistema RAG LouiS.
    """
    logger.info(f"Recebida query: '{query_input.query}', top_k={query_input.top_k}")
    try:
        result = await rag_service.analyze_stroke_location(
            clinical_question=query_input.query,
            top_k=query_input.top_k
        )
        logger.info(f"Resposta gerada para a query: '{query_input.query}'")

        if not isinstance(result, dict) or "answer" not in result or "retrieved_chunks" not in result:
             logger.error(f"Formato de resposta inesperado do RAGService: {result}")
             raise HTTPException(status_code=500, detail="Erro interno ao processar a resposta do RAG.")

        return QueryOutput(
             query=query_input.query,
             answer=result["answer"],
             retrieved_chunks=result["retrieved_chunks"]
        )

    except Exception as e:
        logger.exception(f"Erro ao processar query '{query_input.query}': {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a consulta: {e}")
