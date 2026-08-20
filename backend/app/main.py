import sys
import os

# Garante que o diretório raiz do backend esteja no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.database import Base, engine
import app.models  # noqa: F401 — força o registro dos models no metadata

from app.routes.auth import router as auth_router
from app.routes.filmes import router as filmes_router
from app.routes.favoritos import router as favoritos_router
from app.routes.comentarios import router as comentarios_router

# Cria as tabelas (idempotente se já existirem)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Catálogo de Filmes — Tom Hanks",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas da API
app.include_router(auth_router)
app.include_router(filmes_router)
app.include_router(favoritos_router)
app.include_router(comentarios_router)

# Serve o frontend Angular (arquivos estáticos gerados pelo build)
STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.isdir(STATIC_DIR):
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
