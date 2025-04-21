# Arquivo app/schemas/query.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from backend.app.core.config import settings # Importa para usar o valor padrão de top_k

class QueryInput(BaseModel):
    query: str = Field(..., description="Texto da consulta do usuário")
    top_k: Optional[int] = Field(5, description="Número de chunks a recuperar")

class RetrievedChunk(BaseModel):
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class QueryOutput(BaseModel):
    query: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]

class QueryRequest(BaseModel):
    """
    Schema para a requisição de consulta RAG.
    """
    query: str = Field(..., description="A pergunta ou termo de busca a ser consultado.")
    top_k: Optional[int] = Field(
        settings.DEFAULT_TOP_K,
        description="Número de chunks mais relevantes a serem retornados.",
        gt=0 # Garante que top_k seja maior que 0
    )
    # Você pode adicionar outros filtros aqui, ex: filter_metadata: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Qual a definição de RAG?",
                    "top_k": 3
                }
            ]
        }
    }


class QueryResponse(BaseModel):
    """
    Schema para a resposta da consulta RAG.
    """
    query: str = Field(..., description="A pergunta original feita pelo usuário.")
    answer: str = Field(..., description="A resposta gerada pelo sistema RAG (pode ser apenas os chunks concatenados inicialmente).")
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="Lista dos chunks mais relevantes recuperados.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "O que é FastAPI?",
                    "answer": "FastAPI é um framework web moderno...",
                    "retrieved_chunks": [
                        {
                            "document_id": "aula_python_web.txt",
                            "chunk_id": "aula_python_web.txt_chunk_5",
                            "text": "FastAPI é um framework web moderno, rápido (alta performance), baseado em type hints...",
                            "score": 0.89,
                            "metadata": {"source": "Aula 10", "filename": "aula_python_web.txt"}
                        }
                    ]
                }
            ]
        }
    }