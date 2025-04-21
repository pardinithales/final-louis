from pydantic import BaseModel, Field
from typing import Optional

class ImageInput(BaseModel):
    lesion_site: str = Field(..., description="Localização da lesão para buscar imagem")

class ImageOutput(BaseModel):
    image_url: Optional[str] = Field(None, description="URL da imagem selecionada")
    message: Optional[str] = None # Para casos onde a imagem não é encontrada 