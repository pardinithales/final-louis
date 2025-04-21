# Arquivo app/schemas/transcription.py

"""
Esquemas para comunicação relacionada a documentos clínicos.
"""

from pydantic import BaseModel, Field
from typing import Optional

class UploadResponse(BaseModel):
    """
    Resposta retornada após processamento de upload de documento clínico.
    """
    message: str = Field(..., description="Mensagem de sucesso/confirmação.")
    document_id: str = Field(..., description="ID único do documento processado.")
    chunks_added: int = Field(..., description="Número de chunks criados e armazenados.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Documento clínico processado e armazenado com sucesso!",
                    "document_id": "31. Vascular topographic syndromes – Anterior cerebral artery",
                    "chunks_added": 15
                }
            ]
        }
    }