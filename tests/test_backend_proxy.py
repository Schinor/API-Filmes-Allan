import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_12345678901234567890"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"
os.environ["TMDB_BASE_URL"] = "https://api.themoviedb.org/3"
os.environ["TMDB_API_KEY"] = "fake_tmdb_key"
os.environ["AUTH_SERVICE_URL"] = "http://auth-service:8001"


def setup_catalogo_app():
    for mod in list(sys.modules.keys()):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]

    sys.path.insert(0, os.path.abspath("backend"))

    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import Base, get_db
    from app.dependencies import current_user
    from app.models.comentario import Comentario

    engine_test = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
    Base.metadata.create_all(bind=engine_test)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return app, TestingSessionLocal, current_user, TestClient


def test_catalogo_app_structure():
    app, TestingSessionLocal, current_user, TestClient = setup_catalogo_app()

    app.dependency_overrides[current_user] = lambda: {
        "id": 1,
        "nome": "Allan Teste",
        "email": "allan@teste.com",
        "role": "usuario",
    }

    client = TestClient(app)

    response = client.get("/api/docs")
    assert response.status_code == 200

    fav_list = client.get("/api/favoritos")
    assert fav_list.status_code == 200
    assert isinstance(fav_list.json(), list)

    com_list = client.get("/api/comentarios")
    assert com_list.status_code == 200
    assert isinstance(com_list.json(), list)


def test_rbac_comentarios_dono_outro_usuario_e_admin():
    app, TestingSessionLocal, current_user, TestClient = setup_catalogo_app()
    client = TestClient(app)

    # 1. Usuário 1 logado cria um comentário
    app.dependency_overrides[current_user] = lambda: {
        "id": 1,
        "nome": "Usuario Um",
        "email": "user1@teste.com",
        "role": "usuario",
    }

    create_resp = client.post(
        "/api/comentarios",
        json={"tmdb_movie_id": 100, "texto": "Excelente filme do Tom Hanks!"},
    )
    assert create_resp.status_code == 201
    comentario_id = create_resp.json()["id"]

    # 2. Usuário 2 (role: 'usuario') tenta deletar comentário do Usuário 1 -> 403 Forbidden
    app.dependency_overrides[current_user] = lambda: {
        "id": 2,
        "nome": "Usuario Dois",
        "email": "user2@teste.com",
        "role": "usuario",
    }

    del_user2_resp = client.delete(f"/api/comentarios/{comentario_id}")
    assert del_user2_resp.status_code == 403
    assert (
        del_user2_resp.json()["detail"]
        == "Apenas o autor ou um administrador podem remover este comentário"
    )

    # 3. Usuário 3 (role: 'admin') deleta comentário do Usuário 1 -> 200 OK
    app.dependency_overrides[current_user] = lambda: {
        "id": 99,
        "nome": "Admin Geral",
        "email": "admin@teste.com",
        "role": "admin",
    }

    del_admin_resp = client.delete(f"/api/comentarios/{comentario_id}")
    assert del_admin_resp.status_code == 200
    assert del_admin_resp.json() == {"detail": "Comentário removido"}

    # 4. Criar novo comentário do Usuário 1 e ele mesmo deletar -> 200 OK
    app.dependency_overrides[current_user] = lambda: {
        "id": 1,
        "nome": "Usuario Um",
        "email": "user1@teste.com",
        "role": "usuario",
    }
    create_resp2 = client.post(
        "/api/comentarios",
        json={"tmdb_movie_id": 100, "texto": "Outro comentário para auto-exclusão"},
    )
    assert create_resp2.status_code == 201
    comentario_id_2 = create_resp2.json()["id"]

    del_owner_resp = client.delete(f"/api/comentarios/{comentario_id_2}")
    assert del_owner_resp.status_code == 200
    assert del_owner_resp.json() == {"detail": "Comentário removido"}

    # 5. Tentativa de deletar comentário que não existe -> 404
    del_404_resp = client.delete("/api/comentarios/999999")
    assert del_404_resp.status_code == 404
    assert del_404_resp.json()["detail"] == "Comentário não encontrado"
