from fastapi import APIRouter
from .query import router as query_router
from .image import router as image_router

# Prefixo será adicionado no main.py via app.include_router(..., prefix="/api/v1")
api_router = APIRouter()

# Inclui os routers específicos
api_router.include_router(query_router, prefix="/query", tags=["Query"])
api_router.include_router(image_router, prefix="/image", tags=["Image"])
