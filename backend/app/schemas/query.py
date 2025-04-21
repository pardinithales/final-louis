# Arquivo app/schemas/query.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from backend.app.core.config import settings # Importa para usar o valor padrão de top_k

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


class RetrievedChunk(BaseModel):
    """
    Schema para representar um chunk de texto recuperado pelo RAG.
    """
    document_id: str = Field(..., description="Identificador do documento original do chunk.")
    chunk_id: str = Field(..., description="Identificador único do chunk dentro do banco de vetores.")
    text: str = Field(..., description="O conteúdo textual do chunk.")
    score: float = Field(..., description="Pontuação de relevância do chunk em relação à consulta (ex: similaridade de cosseno).")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados associados ao chunk (ex: source, filename).")


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