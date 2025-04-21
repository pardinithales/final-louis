# Arquivo README.md

# LouiS Stroke - Sistema de Localização Neurológica em AVC

**Sistema RAG especializado em neurologia para localização de AVC utilizando FastAPI e interface web.**

Este projeto implementa um sistema de Retrieval-Augmented Generation (RAG) que permite fazer upload de documentos clínicos sobre síndromes vasculares e obter localizações neuroanatômicas precisas. O backend é construído com FastAPI e utiliza ChromaDB para armazenar e buscar embeddings dos documentos. Uma interface com Streamlit permite interagir com o sistema.

## Funcionalidades

*   **Upload de Documentos Clínicos:** Endpoint para adicionar novos documentos ao sistema.
*   **Busca Semântica:** Endpoint para realizar consultas em linguagem natural sobre localizações neurológicas em AVC.
*   **Interface Web:** Aplicação Streamlit para facilitar a interação (upload e consulta).

## Estrutura do Projeto

*   `backend/`: Contém toda a lógica do backend da aplicação.
    *   `app/`: Código principal da API FastAPI.
        *   `main.py`: Ponto de entrada da aplicação FastAPI.
        *   `core/`: Configurações da aplicação.
        *   `routers/`: Endpoints da API (upload, query).
        *   `schemas/`: Modelos Pydantic para validação de dados da API.
        *   `services/`: Lógica de negócio (RAG, interação com Vector Store).
    *   `image_selector.py`: Serviço para seleção dinâmica de imagens para as síndromes.
    *   `load_chapters.py`: Script para carregar documentos da pasta chapters.
    *   `reset_db.py`: Utilitário para reiniciar o banco de dados ChromaDB.
*   `chapters/`: Documentos clínicos sobre síndromes vasculares.
*   `images/`: Imagens de diagramas neurológicos para as síndromes.
*   `data/`: Diretório para armazenamento persistente do ChromaDB.
*   `ui/`: Código da interface Streamlit.
*   `.env`: Arquivo para variáveis de ambiente.
*   `requirements.txt`: Dependências Python do projeto.
*   `start_api.py`: Script para iniciar a API.
*   `app.py`: Script para iniciar a interface Streamlit.

## Instalação

> **Importante:** Este projeto requer Python 3.11 para funcionar corretamente. Outras versões podem causar problemas de compatibilidade com algumas dependências.

1.  **Clone o repositório:**
    ```bash
    git clone <url_do_repositorio>
    cd louis_stroke
    ```

2.  **Crie e ative um ambiente virtual com Python 3.11:**
    ```bash
    # Certifique-se de estar usando Python 3.11
    python -V  # Deve mostrar Python 3.11.x
    
    # Se tiver múltiplas versões instaladas, especifique a 3.11:
    python3.11 -m venv .venv
    
    # Windows
    .\.venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    *   Copie o arquivo `.env.example` para `.env` (se existir) ou crie um arquivo `.env`.
    *   Ajuste as variáveis conforme necessário.

## Execução

1.  **Execute o backend FastAPI:**
    ```bash
    python start_api.py
    ```
    A API estará disponível em `http://localhost:8000`. A documentação interativa (Swagger UI) pode ser acessada em `http://localhost:8000/docs`.

2.  **Execute a interface Streamlit:**
    Abra um *novo terminal*, ative o ambiente virtual e execute:
    ```bash
    python app.py
    ```
    A interface estará disponível em `http://localhost:8501` (ou outra porta indicada pelo Streamlit).

## Carregamento de Documentos

Para carregar os documentos clínicos da pasta `chapters/`:

```bash
cd backend
python load_chapters.py
```

## Resetar o Banco de Dados

Para reiniciar o banco de dados ChromaDB:

```bash
cd backend
python reset_db.py