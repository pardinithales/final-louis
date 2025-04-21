"""
Este arquivo facilita a execução do aplicativo Streamlit diretamente da raiz do projeto.
Simplesmente chama o aplicativo principal que está em ui/streamlit_app.py
"""

import os
import sys
import subprocess

def main():
    """Executa o aplicativo Streamlit."""
    streamlit_app_path = os.path.join("ui", "streamlit_app.py")
    if os.path.exists(streamlit_app_path):
        # Adiciona o diretório atual ao PYTHONPATH para garantir importações corretas
        sys.path.insert(0, os.getcwd())
        
        # Executa o streamlit run com o caminho correto
        subprocess.run(["streamlit", "run", streamlit_app_path])
    else:
        print(f"Erro: Arquivo {streamlit_app_path} não encontrado.")
        print("Verifique se você está no diretório raiz do projeto.")
        sys.exit(1)

if __name__ == "__main__":
    main() 