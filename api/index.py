#!/usr/bin/env python3
"""
Ponto de entrada para o deploy no Vercel da API LouiS Stroke.
"""
# Hack para sqlite3 ANTES de qualquer importação que possa usar chromadb
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import sys

# Adiciona o diretório raiz ao path para permitir importações relativas adequadas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Importa a aplicação FastAPI definida em backend/app/main.py
from backend.app.main import app as main_app

# Criação do objeto app para o Vercel
app = main_app

# Configuração de CORS para permitir acesso da aplicação frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler para erros não tratados
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro interno do servidor: {str(exc)}"}
    )

# Se este arquivo for executado diretamente (para testes locais)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)
