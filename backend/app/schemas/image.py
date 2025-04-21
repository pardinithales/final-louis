from pydantic import BaseModel, Field
from typing import Optional

class ImageInput(BaseModel):
    lesion_site: Optional[str] = Field(None, description="Localização da lesão para buscar imagem")
    image_name: Optional[str] = Field(None, description="Nome exato do arquivo de imagem para buscar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lesion_site": "Medulla",
                "image_name": None
            }
        }
        
    # Garantir que pelo menos um dos campos foi preenchido
    @classmethod
    def validate(cls, values):
        if not values.get("lesion_site") and not values.get("image_name"):
            raise ValueError("Deve fornecer 'lesion_site' ou 'image_name'")
        return values

class ImageOutput(BaseModel):
    image_url: Optional[str] = Field(None, description="URL da imagem selecionada")
    message: Optional[str] = None # Para casos onde a imagem não é encontrada 