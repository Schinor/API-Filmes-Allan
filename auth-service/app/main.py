import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
import app.models  # força o registro dos models no metadata

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router

# Cria tabelas caso não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microsserviço de Autenticação — Filmes Tom Hanks",
    description="Serviço interno de autenticação, usuários e recuperação de senha.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "auth-service",
        "version": "1.0.0",
    }


# Rotas
app.include_router(auth_router)
app.include_router(users_router)
