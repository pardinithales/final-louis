import logging
from fastapi import APIRouter, HTTPException

# Supondo que a lógica está em image_selector ou será movida para um serviço
# Se estiver diretamente em image_selector.py na raiz do backend:
try:
    # Tenta importar a função específica do módulo na raiz do backend
    from backend.image_selector import select_image_for_lesion
except ImportError:
    # Fallback ou tratamento de erro se o módulo/função não existir
    logging.warning("Módulo backend.image_selector ou função select_image_for_lesion não encontrada.")
    async def select_image_for_lesion(lesion_site: str) -> str | None:
        # Retornar placeholder ou None se a lógica real não estiver disponível
        # Implemente um retorno padrão ou levante um erro se for crítico
        return None

from backend.app.schemas.image import ImageInput, ImageOutput

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/select", # O prefixo /api/v1/image será adicionado no __init__
    response_model=ImageOutput,
    summary="Seleciona imagem por local da lesão",
    description="Retorna a URL de uma imagem relevante para o local da lesão fornecido.",
    tags=["Image"]
)
async def select_image(
    image_input: ImageInput
):
    """
    Endpoint para selecionar uma imagem baseada no local da lesão.
    """
    logger.info(f"Recebida solicitação de imagem para lesão: '{image_input.lesion_site}'")
    try:
        # Chamar a função que busca a imagem
        # Usamos await pois a função pode ser assíncrona no futuro
        image_filename = await select_image_for_lesion(image_input.lesion_site)

        if image_filename:
            # Assume que as imagens estão em /static/images/
            # IMPORTANTE: Requer configuração de StaticFiles em main.py
            image_url = f"/static/images/{image_filename}" # Exemplo
            logger.info(f"Imagem encontrada para '{image_input.lesion_site}': {image_url}")
            return ImageOutput(image_url=image_url)
        else:
            logger.warning(f"Nenhuma imagem encontrada para '{image_input.lesion_site}'")
            return ImageOutput(image_url=None, message="Imagem não encontrada para este local.")

    except Exception as e:
        logger.exception(f"Erro ao processar seleção de imagem para '{image_input.lesion_site}': {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao selecionar imagem: {e}") 