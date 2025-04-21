# Dockerfile para backend FastAPI
FROM python:3.12-slim

# Cria diretório de trabalho
WORKDIR /app

# Copia requirements.txt e instala dependências
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY ./app ./app

# Cria usuário não-root
RUN useradd -m appuser
USER appuser

# Expõe porta padrão do FastAPI
EXPOSE 8000

# Entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
