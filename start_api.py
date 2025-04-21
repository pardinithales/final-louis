#!/usr/bin/env python3
"""
Script para iniciar a API LouiS Stroke.
Adiciona o diretório do projeto ao PYTHONPATH para garantir as importações corretas.
"""
import os
import sys
import subprocess

def main():
    """Executa a API FastAPI usando uvicorn."""
    # Obtém o diretório onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Adiciona o diretório do script ao PYTHONPATH
    sys.path.insert(0, script_dir)
    
    # Verifica se estamos no diretório do projeto ou não
    if not os.path.isdir(os.path.join(script_dir, "backend")):
        print(f"Erro: Diretório 'backend' não encontrado em {script_dir}")
        print("Verifique se você está executando o script do diretório correto.")
        sys.exit(1)
    
    # Comando para executar a API
    cmd = ["uvicorn", "backend.app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    
    print(f"Iniciando a API LouiS Stroke a partir de: {script_dir}")
    print(f"Comando: {' '.join(cmd)}")
    
    # Executa a API a partir do diretório do script
    os.chdir(script_dir)
    subprocess.run(cmd)

if __name__ == "__main__":
    main() 