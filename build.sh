#!/bin/bash

# Script de build para o Vercel
echo "Iniciando script de build para o Vercel..."

# Criar diretório para imagens estáticas se não existir
mkdir -p static/images

# Copiar imagens para o diretório static
if [ -d "images" ]; then
  echo "Copiando imagens para diretório static..."
  cp -r images/* static/images/
  echo "Imagens copiadas com sucesso!"
else
  echo "Diretório de imagens não encontrado!"
fi

# Instalar dependências específicas para o Vercel
echo "Instalando dependências..."
pip install -r requirements-vercel.txt

echo "Build concluído com sucesso!"
