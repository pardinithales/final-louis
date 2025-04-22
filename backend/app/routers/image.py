import logging
import os
from fastapi import APIRouter, HTTPException
from typing import List

# Importação corrigida do módulo image_selector
from backend.image_selector import get_image_by_exact_name, select_image_for_syndrome, get_available_images

from backend.app.schemas.image import ImageInput, ImageOutput

logger = logging.getLogger(__name__)
router = APIRouter()

# Diretório de imagens - ajustar conforme configuração do projeto
# Aqui assumimos que o diretório de imagens está na raiz do projeto
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
IMAGES_DIR = os.path.join(script_dir, "images")

@router.post(
    "/select",
    response_model=ImageOutput,
    summary="Seleciona imagem por local da lesão ou nome exato",
    description="Retorna a URL de uma imagem com base no local da lesão ou no nome exato do arquivo.",
    tags=["Image"]
)
async def select_image(
    image_input: ImageInput
):
    """
    Endpoint para selecionar uma imagem baseada no local da lesão ou nome exato.
    
    Se image_name for fornecido, busca diretamente essa imagem na pasta de imagens.
    Se apenas lesion_site for fornecido, usa IA para selecionar a imagem mais adequada.
    """
    try:
        # Verificar se temos imagens disponíveis
        available = get_available_images()
        logger.info(f"Imagens disponíveis: {len(available)}")
        if len(available) > 0:
            logger.info(f"Primeiras 5 imagens: {available[:5]}")
        
        # Verificar se o usuário forneceu o nome exato da imagem
        if image_input.image_name:
            logger.info(f"Buscando imagem pelo nome exato: '{image_input.image_name}'")
            
            # Usar a função get_image_by_exact_name do módulo image_selector
            result = get_image_by_exact_name(image_input.image_name)
            
            if result:
                # Ajustar URL para o formato esperado pela aplicação
                # A URL já vem formatada de get_image_by_exact_name
                image_url = result['image_url'] 
                logger.info(f"Imagem encontrada: {image_url}")
                return ImageOutput(image_url=image_url, message=result.get('message'))
            else:
                logger.warning(f"Imagem não encontrada com o nome: {image_input.image_name}")
                return ImageOutput(image_url=None, message=f"Imagem '{image_input.image_name}' não encontrada.")
        
        # Se não tiver o nome da imagem, busca pelo local da lesão usando IA ou diretamente se o nome contiver extensão
        elif image_input.lesion_site:
            lesion_site = image_input.lesion_site
            logger.info(f"Buscando imagem pelo local da lesão: '{lesion_site}'")
            
            # Verificar primeiro se o lesion_site corresponde exatamente a alguma imagem disponível
            for img in available:
                img_name_no_ext = os.path.splitext(img)[0]
                if img_name_no_ext == lesion_site or img == lesion_site:
                    logger.info(f"Correspondência direta encontrada: {img}")
                    return ImageOutput(image_url=f"/static/images/{img}")
                    
            # Verifica se o valor fornecido parece ser um nome de arquivo (com extensão .png)
            if lesion_site.lower().endswith('.png'):
                logger.info(f"O valor fornecido parece ser um nome de arquivo: '{lesion_site}'")
                # Buscar diretamente nos arquivos disponíveis
                for img in available:
                    if img.lower() == lesion_site.lower():
                        logger.info(f"Correspondência case-insensitive encontrada: {img}")
                        return ImageOutput(image_url=f"/static/images/{img}")
                
                logger.warning(f"Imagem não encontrada com o nome: {lesion_site}")
            
            # Caso contrário, tenta buscar usando IA
            if len(available) > 0:  # Só tenta usar IA se houver imagens disponíveis
                image_filename = await select_image_for_syndrome(lesion_site)
                
                if not image_filename:
                    logger.warning(f"Nenhuma imagem encontrada para '{lesion_site}'")
                    return ImageOutput(image_url=None, message=f"Imagem não encontrada para o local: {lesion_site}")
                
                # Verificar se o resultado é um nome de arquivo ou um caminho completo
                if os.path.isabs(image_filename):
                    image_name = os.path.basename(image_filename)
                else:
                    image_name = image_filename
                
                # Gerar URL da imagem
                image_url = f"/static/images/{image_name}"
                logger.info(f"URL da imagem gerada: {image_url}")
                return ImageOutput(image_url=image_url)
            else:
                logger.warning("Não há imagens disponíveis para seleção")
                return ImageOutput(image_url=None, message="Não há imagens disponíveis no sistema")
        
        else:
            # Este caso deve ser capturado pela validação do Pydantic, mas mantemos como segurança
            return ImageOutput(image_url=None, message="Deve fornecer 'lesion_site' ou 'image_name'")

    except Exception as e:
        logger.exception(f"Erro ao processar seleção de imagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao selecionar imagem: {e}")

@router.get(
    "/list",
    response_model=List[str],
    summary="Lista todas as imagens disponíveis",
    description="Retorna uma lista com os nomes de todas as imagens disponíveis no sistema.",
    tags=["Image"]
)
async def list_images():
    """
    Endpoint para listar todas as imagens disponíveis no sistema.
    """
    try:
        available_images = get_available_images()
        
        # Retorna apenas os nomes dos arquivos, não os caminhos completos
        image_names = [os.path.basename(img) for img in available_images]
        return image_names
    except Exception as e:
        logger.exception(f"Erro ao listar imagens disponíveis: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao listar imagens: {e}") 