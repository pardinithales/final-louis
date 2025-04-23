# final-louis/Dockerfile

# Use uma imagem base oficial do Python 3.11 slim
FROM python:3.11-slim

# Defina variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Instale dependências do sistema, se necessário (ex: build-essentials para algumas libs)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

# Copie o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instale as dependências Python
# --no-cache-dir para manter a imagem menor
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copie todo o conteúdo do diretório local ANTES de executar scripts
COPY . .

# Execute o script load_chapters.py durante o build
RUN python backend/load_chapters.py

# Exponha a porta que a aplicação FastAPI usa (definida em start_api.py ou uvicorn command)
EXPOSE 8000

# Comando para iniciar a aplicação FastAPI em produção (sem --reload)
# Ajuste o caminho 'backend.app.main:app' se a estrutura do seu projeto for diferente
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]