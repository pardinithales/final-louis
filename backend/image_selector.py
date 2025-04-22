#!/usr/bin/env python3
"""
Script para selecionar imagens para o sistema LouiS Stroke.
Obtém dinamicamente todas as imagens da pasta ./images e
usa IA para selecionar a imagem mais adequada para uma localização neuroanatômica.
"""

import os
import logging
import json
import re
import random
from typing import List, Optional, Dict, Tuple, Union
from openai import AsyncOpenAI
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Obter o caminho absoluto para o diretório images usando o caminho do script atual
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Subir um nível para a raiz do projeto

# -- Definição dos Diretórios de Imagens --
# Diretório onde o FastAPI serve os arquivos estáticos (relativo ao script atual)
# image_selector.py está em 'backend/', main.py está em 'backend/app/'
# O diretório estático é 'backend/app/static/images'
APP_STATIC_IMAGES_DIR = os.path.abspath(os.path.join(script_dir, "app", "static", "images"))

# Diretório original das imagens na raiz do projeto (usado para sincronização)
SOURCE_IMAGES_DIR = os.path.abspath(os.path.join(project_root, "images"))

# Outros diretórios possíveis (menos prováveis, mas mantidos como fallback)
LEGACY_IMAGES_DIR_BACKEND = os.path.abspath(os.path.join(script_dir, "images"))
LEGACY_IMAGES_DIR_ROOT_STATIC = os.path.abspath(os.path.join(project_root, "static", "images"))
# -----------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Lista para armazenar caminhos de imagens disponíveis
available_images = []
# Novo: dicionário para mapeamento case-insensitive
image_name_map = {}

def clear_available_images_cache():
    """
    Limpa o cache da lista de imagens disponíveis, forçando uma nova busca na próxima chamada.
    """
    global available_images, image_name_map
    available_images = []
    image_name_map = {}
    logger.info("Cache de imagens disponíveis limpo.")

def get_available_images() -> List[str]:
    """
    Obtém a lista de imagens disponíveis, priorizando o diretório servido pelo FastAPI.
    Também constrói o dicionário de mapeamento case-insensitive.
    Returns:
        List[str]: Lista com os nomes das imagens encontradas (não os caminhos completos)
    """
    global available_images, image_name_map
    if available_images and image_name_map:
        logger.info(f"Retornando {len(available_images)} imagens do cache")
        return available_images

    # Definir a ordem de prioridade dos diretórios
    # 1. Diretório servido pelo FastAPI (mais importante)
    # 2. Diretório original na raiz (fonte da sincronização)
    # 3. Diretórios legados/fallback
    search_dirs = [
        APP_STATIC_IMAGES_DIR, 
        SOURCE_IMAGES_DIR,
        LEGACY_IMAGES_DIR_ROOT_STATIC,
        LEGACY_IMAGES_DIR_BACKEND,
    ]

    logger.info(f"Buscando imagens nos diretórios (priorizados): {search_dirs}")

    # Buscar imagens na ordem de prioridade
    for img_dir in search_dirs:
        if os.path.exists(img_dir):
            try:
                # Lista todos os arquivos com extensão .png no diretório de imagens
                # Usar listdir para garantir que o case original seja capturado
                image_files = [f for f in os.listdir(img_dir) 
                               if os.path.isfile(os.path.join(img_dir, f)) and f.lower().endswith('.png')]

                if image_files:
                    logger.info(f"Encontradas {len(image_files)} imagens no diretório prioritário: {img_dir}")
                    # Armazena apenas os nomes dos arquivos (com case original)
                    available_images = image_files
                    # Construir dicionário de mapeamento case-insensitive -> case original
                    image_name_map = {img.lower(): img for img in image_files}
                    return available_images
                else:
                    logger.debug(f"Nenhuma imagem .png encontrada em: {img_dir}")
            except OSError as e:
                logger.error(f"Erro ao acessar o diretório {img_dir}: {e}")
        else:
            logger.debug(f"Diretório não encontrado, pulando: {img_dir}")

    logger.warning("Nenhuma imagem encontrada em nenhum dos diretórios de busca.")
    available_images = []
    image_name_map = {}
    return []

def get_image_by_exact_name(image_name: str) -> Optional[Dict[str, str]]:
    """
    Busca uma imagem pelo nome exato (com ou sem extensão), de forma case-insensitive.
    """
    get_available_images()  # Garante que image_name_map está atualizado
    global image_name_map
    # Remove a extensão .png, se presente
    if image_name.lower().endswith('.png'):
        search_name = image_name[:-4]
    else:
        search_name = image_name
    # Busca case-insensitive no dicionário
    key = f"{search_name}.png".lower()
    if key in image_name_map:
        real_name = image_name_map[key]
        image_url = f"/static/images/{real_name}"
        logger.info(f"Imagem encontrada (case-insensitive): {real_name}")
        return {"image_url": image_url, "message": f"Imagem encontrada: {real_name}"}
    logger.warning(f"Nenhuma imagem encontrada com o nome: {image_name}")
    return None

async def select_image_for_syndrome(lesion_site: str) -> Optional[str]:
    """
    Seleciona uma imagem para a localização anatômica fornecida usando IA
    
    Args:
        lesion_site: String com a localização anatômica da lesão
        
    Returns:
        Nome do arquivo de imagem ou None se falhar
    """
    try:
        get_available_images()  # Garante que image_name_map está atualizado
        global image_name_map, available_images
        # Obter lista atualizada de imagens
        if not available_images:
            logger.warning("Não há imagens disponíveis para seleção")
            return None
            
        # Inicializar cliente OpenAI
        ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Construir prompt específico
        prompt = (
            "INSTRUÇÃO:\n"
            "Selecione EXATAMENTE um arquivo .png da LISTA DE ARQUIVOS DISPONÍVEIS que melhor represente "
            "a localização neuroanatômica da lesão.\n\n"
            "REGRAS DE SELEÇÃO (EM ORDEM DE PRIORIDADE):\n"
            "1. Escolha a imagem que contenha o nome da ARTÉRIA mais específica relacionada à lesão\n"
            "2. Se não encontrar artéria específica, escolha imagem com SÍNDROME relacionada\n"
            "3. Em último caso, escolha imagem com ESTRUTURA ANATÔMICA relacionada\n\n"
            "DADOS DO CASO:\n"
            f"• Localização: '{lesion_site}'\n"
            f"• Artéria: '{locals().get('artery', '')}'\n"
            f"• Síndrome: '{locals().get('syndrome', '')}'\n\n"
            "RETORNE APENAS:\n"
            "• Nome exato do arquivo com extensão .png\n"
            "• Sem texto adicional ou explicações\n\n"
            "ARQUIVOS DISPONÍVEIS:\n"
            f"{', '.join(available_images)}"
        )
        
        # Fazer chamada à API
        completion = await ai_client.chat.completions.create(
            model="gpt-4o",  # Usando modelo avançado para precisão
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Baixa temperatura para resultados determinísticos
            max_tokens=50,    # Limitar tokens para evitar explicações
        )
        
        # Extrair resposta
        response = completion.choices[0].message.content.strip()
        
        # -------------------------------
        # Normalizar extensão do arquivo
        # -------------------------------
        # Garante que exista **somente** uma extensão .png no final da string
        # Remove repetições (ex.: "img.png.png" → "img.png") ou adiciona se faltar
        if re.search(r"(?i)(\.png){2,}$", response):  # duas ou mais ocorrências
            response = re.sub(r"(?i)(\.png)+$", ".png", response)
        elif not response.lower().endswith('.png'):
            response = f"{response}.png"
        
        # Busca case-insensitive no dicionário
        key = response.lower()
        if key in image_name_map:
            real_name = image_name_map[key]
            logger.info(f"Imagem selecionada com sucesso (case-insensitive): {real_name}")
            return real_name
        else:
            # Tentar encontrar correspondência parcial (fallback)
            for image in available_images:
                if image.lower() == response.lower():
                    logger.info(f"Imagem encontrada por correspondência case-insensitive: {image}")
                    return image
            
            logger.warning(f"IA retornou '{response}', que não corresponde a nenhum arquivo disponível")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao selecionar imagem: {e}")
        return None


async def process_syndrome_response(llm_response: str) -> str:
    """
    Processa a resposta do LLM para adicionar a imagem apropriada
    
    Args:
        llm_response: String com a resposta do LLM contendo síndromes
        
    Returns:
        Resposta aprimorada com a linha da imagem adicionada
    """
    try:
        # Extrair lista JSON de síndromes
        syndrome_list_match = re.search(r'Lista de síndromes: (\[.*?\])', llm_response, re.DOTALL)
        if not syndrome_list_match:
            logger.warning("Não foi possível extrair a lista de síndromes da resposta")
            return llm_response
        
        # Decodificar JSON para obter as síndromes
        syndromes_json = syndrome_list_match.group(1)
        syndromes = json.loads(syndromes_json)
        
        # Verificar se temos pelo menos uma síndrome
        if not syndromes or len(syndromes) == 0:
            logger.warning("Lista de síndromes vazia")
            return llm_response
        
        # Pegar a primeira síndrome (a mais relevante)
        top_syndrome = syndromes[0]
        lesion_site = top_syndrome.get("lesion_site", "").strip()
        
        if not lesion_site:
            logger.warning("Lesion site não encontrado na primeira síndrome")
            return llm_response
        
        # Selecionar imagem usando IA
        selected_image = await select_image_for_syndrome(lesion_site)
        
        # Inserir a imagem na resposta
        if selected_image:
            # Inserir a linha da imagem após a lista de síndromes
            parts = llm_response.split("Notas:", 1)
            if len(parts) == 2:
                enhanced_response = f"{parts[0]}Imagem: {selected_image}\nNotas:{parts[1]}"
                return enhanced_response
        
        return llm_response
    except Exception as e:
        logger.error(f"Erro ao processar resposta: {e}")
        return llm_response


# Exemplo de uso como script independente
if __name__ == "__main__":
    import asyncio
    
    async def test_script():
        # Listar imagens disponíveis
        images = get_available_images()
        print(f"Imagens disponíveis: {len(images)}")
        for img in images[:5]:  # Mostrar apenas as 5 primeiras para exemplo
            print(f" - {img}")
        
        # Testar seleção de imagem
        test_lesion = "Anterior Cerebral Artery"
        selected = await select_image_for_syndrome(test_lesion)
        print(f"\nLocalização: '{test_lesion}'")
        print(f"Imagem selecionada: {selected}")
        
    # Executar teste
    asyncio.run(test_script()) 