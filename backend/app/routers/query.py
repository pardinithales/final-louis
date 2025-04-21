import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.query import QueryRequest, QueryResponse, RetrievedChunk
from backend.app.services.rag_service import RAGService, get_rag_service

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Analisa casos clínicos para localização de AVC",
    description="Recebe dados clínicos e retorna informações precisas sobre síndromes vasculares e localizações neuroanatômicas.",
)
async def query_stroke_localization(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    """
    Endpoint RAG para análise de localização de AVC (LouiS Stroke).
    """
    if not request.query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A consulta clínica não pode estar vazia.",
        )

    try:
        result = await rag_service.analyze_stroke_location(
            clinical_question=request.query, top_k=request.top_k
        )

        return QueryResponse(
            query=request.query,
            answer=result["answer"],
            retrieved_chunks=result["retrieved_chunks"],
        )

    except Exception as exc:
        logger.exception("Erro ao processar análise de AVC: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno ao processar sua consulta de localização neurológica: {exc}",
        )
