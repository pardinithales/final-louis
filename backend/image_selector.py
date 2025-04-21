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
IMAGES_DIR = os.path.join(project_root, "images")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuração de caminhos
# Base dir é o diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
IMAGES_FOLDER = os.path.join(BASE_DIR, "images")
STATIC_IMAGES_FOLDER = os.path.join(BASE_DIR, "static", "images")

# Verificar se o diretório de imagens existe
if not os.path.exists(IMAGES_FOLDER):
    logger.warning(f"O diretório de imagens não foi encontrado: {IMAGES_FOLDER}")

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
    Obtém a lista de imagens disponíveis no diretório de imagens.
    Também constrói o dicionário de mapeamento case-insensitive.
    Returns:
        List[str]: Lista com os nomes das imagens encontradas (não os caminhos completos)
    """
    global available_images, image_name_map
    if available_images and image_name_map:
        logger.info(f"Retornando {len(available_images)} imagens do cache")
        return available_images
    
    # Caminho base do projeto - diretório raiz
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Verificar múltiplos possíveis diretórios para as imagens
    possible_dirs = [
        os.path.join(base_path, "images"),             # [raiz]/images
        os.path.join(base_path, "static", "images"),   # [raiz]/static/images
        os.path.join(os.path.dirname(__file__), "images"),           # backend/images
        os.path.join(os.path.dirname(__file__), "static", "images"), # backend/static/images
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images"), # [raiz]/backend/static/images
    ]
    
    logger.info(f"Buscando imagens nos diretórios: {possible_dirs}")
    
    # Buscar imagens em todos os diretórios possíveis
    for img_dir in possible_dirs:
        if os.path.exists(img_dir):
            # Lista todos os arquivos com extensão .png no diretório de imagens
            image_files = [f for f in os.listdir(img_dir) if f.lower().endswith('.png')]
            
            if image_files:
                logger.info(f"Encontradas {len(image_files)} imagens no diretório {img_dir}")
                # Armazena apenas os nomes dos arquivos (não os caminhos completos)
                available_images = image_files
                # Novo: construir dicionário de mapeamento case-insensitive
                image_name_map = {img.lower(): img for img in image_files}
                return available_images
    
    logger.warning("Nenhuma imagem encontrada em nenhum dos diretórios possíveis")
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
        image_url = f"/images/{real_name}"
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
            f"INSTRUÇÃO: Selecione exatamente um nome de arquivo da lista abaixo que melhor "
            f"corresponda ao local anatômico: '{lesion_site}'.\n"
            f"Retorne APENAS o nome EXATO do arquivo, sem texto adicional, sem explicações, "
            f"sem formatação especial, apenas o nome do arquivo com a extensão .png.\n\n"
            f"LISTA DE ARQUIVOS DISPONÍVEIS:\n"
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