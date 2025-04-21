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
from typing import List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

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


async def get_available_images() -> List[str]:
    """
    Obtém lista atual de todas as imagens na pasta ./images
    
    Returns:
        Lista de nomes dos arquivos PNG
    """
    try:
        # Verificar se a pasta existe
        if not os.path.exists(IMAGES_DIR):
            logger.error(f"Diretório {IMAGES_DIR} não encontrado")
            return []
            
        # Listar todos os arquivos PNG na pasta
        image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(".png")]
        logger.info(f"Encontradas {len(image_files)} imagens em {IMAGES_DIR}")
        return image_files
    except Exception as e:
        logger.error(f"Erro ao obter imagens disponíveis: {e}")
        return []


async def select_image_for_syndrome(lesion_site: str) -> Optional[str]:
    """
    Seleciona uma imagem para a localização anatômica fornecida usando IA
    
    Args:
        lesion_site: String com a localização anatômica da lesão
        
    Returns:
        Nome do arquivo de imagem ou None se falhar
    """
    try:
        # Obter lista atualizada de imagens
        available_images = await get_available_images()
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
        
        # Verificar se a resposta é um dos arquivos disponíveis
        if response in available_images:
            logger.info(f"Imagem selecionada com sucesso: {response}")
            return response
        else:
            # Tentar encontrar correspondência parcial
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
        images = await get_available_images()
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