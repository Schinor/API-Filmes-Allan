import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect
from app.core.database import Base, engine
import app.models  # força o registro dos models no metadata

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router


def init_db():
    # Cria tabelas não existentes
    Base.metadata.create_all(bind=engine)
    
    # Executa verificação e migração automática de colunas para bancos pré-existentes
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "usuarios" in inspector.get_table_names():
                columns = [c["name"] for c in inspector.get_columns("usuarios")]
                if "role" not in columns:
                    conn.execute(
                        text("ALTER TABLE usuarios ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'usuario'")
                    )
                    conn.commit()
    except Exception as e:
        print(f"[auth-service] Aviso ao verificar schema do banco: {e}")


init_db()

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
