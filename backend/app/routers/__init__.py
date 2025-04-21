from fastapi import APIRouter
from .query import router as query_router
from .documents import router as document_router

# Router principal que agrupa todos os sub-routers
api_router = APIRouter(prefix="/api/v1")

# Inclui os routers específicos
api_router.include_router(query_router, prefix="/query", tags=["Query"])
api_router.include_router(document_router, tags=["Documents"])
