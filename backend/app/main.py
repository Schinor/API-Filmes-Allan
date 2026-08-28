import sys
import os

# Garante que o diretório raiz do backend esteja no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Serve o frontend Angular (SPA fallback para suporte a HTML5 pushState routing)
STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.isdir(STATIC_DIR):
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

if os.path.isdir(STATIC_DIR):
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Se for um arquivo estático existente (JS, CSS, PNG, ICO, etc.)
        target = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(target):
            return FileResponse(target)

        # Para qualquer rota do cliente (ex: /reset-password, /login, /catalogo), serve o index.html
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return FileResponse(target)
