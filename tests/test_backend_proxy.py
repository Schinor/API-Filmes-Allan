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
    from app.models.favoritos import Favorito

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
        "role": "houston-temos-acesso",
        "permissions": ["assistir:catalogo", "listar:favoritos", "listar:comentarios"],
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


def test_rbac_permissoes_amigo_do_wilson_e_terminal():
    app, TestingSessionLocal, current_user, TestClient = setup_catalogo_app()
    client = TestClient(app)

    # 1. Amigo do Wilson tenta favoritar filme -> 403 Forbidden
    app.dependency_overrides[current_user] = lambda: {
        "id": 10,
        "nome": "Wilson User",
        "email": "wilson@teste.com",
        "role": "amigo-do-wilson",
        "permissions": ["assistir:catalogo", "detalhes:filmes", "listar:comentarios"],
    }

    fav_resp = client.post(
        "/api/favoritos",
        json={"tmdb_movie_id": 550, "titulo": "Fight Club", "poster_path": "/path.jpg"},
    )
    assert fav_resp.status_code == 403
    assert "adicionar:favoritos" in fav_resp.json()["detail"]

    # 2. Preso no Terminal pode favoritar, mas não pode comentar -> 403 Forbidden
    app.dependency_overrides[current_user] = lambda: {
        "id": 20,
        "nome": "Terminal User",
        "email": "terminal@teste.com",
        "role": "preso-no-terminal",
        "permissions": [
            "assistir:catalogo",
            "detalhes:filmes",
            "listar:comentarios",
            "listar:favoritos",
            "adicionar:favoritos",
            "remover:favoritos",
        ],
    }

    fav_ok = client.post(
        "/api/favoritos",
        json={"tmdb_movie_id": 550, "titulo": "Fight Club", "poster_path": "/path.jpg"},
    )
    assert fav_ok.status_code == 201

    com_resp = client.post(
        "/api/comentarios",
        json={"tmdb_movie_id": 550, "texto": "Tentativa de comentário no Terminal"},
    )
    assert com_resp.status_code == 403
    assert "criar:comentarios" in com_resp.json()["detail"]


def test_rbac_comentarios_dono_outro_usuario_e_admin():
    app, TestingSessionLocal, current_user, TestClient = setup_catalogo_app()
    client = TestClient(app)

    # 1. Usuário 1 (Houston) cria um comentário
    app.dependency_overrides[current_user] = lambda: {
        "id": 1,
        "nome": "Usuario Um",
        "email": "user1@teste.com",
        "role": "houston-temos-acesso",
        "permissions": ["criar:comentarios", "apagar:comentario-proprio", "listar:comentarios"],
    }

    create_resp = client.post(
        "/api/comentarios",
        json={"tmdb_movie_id": 100, "texto": "Excelente filme do Tom Hanks!"},
    )
    assert create_resp.status_code == 201
    comentario_id = create_resp.json()["id"]

    # 2. Usuário 2 (Houston) tenta deletar comentário do Usuário 1 -> 403 Forbidden
    app.dependency_overrides[current_user] = lambda: {
        "id": 2,
        "nome": "Usuario Dois",
        "email": "user2@teste.com",
        "role": "houston-temos-acesso",
        "permissions": ["criar:comentarios", "apagar:comentario-proprio", "listar:comentarios"],
    }

    del_user2_resp = client.delete(f"/api/comentarios/{comentario_id}")
    assert del_user2_resp.status_code == 403
    assert (
        del_user2_resp.json()["detail"]
        == "Apenas o autor ou um administrador podem remover este comentário"
    )

    # 3. Usuário 3 (Admin) deleta comentário do Usuário 1 -> 200 OK
    app.dependency_overrides[current_user] = lambda: {
        "id": 99,
        "nome": "Admin Geral",
        "email": "admin@teste.com",
        "role": "admin",
        "permissions": ["apagar:comentario-de-outro", "administrar:sistema"],
    }

    del_admin_resp = client.delete(f"/api/comentarios/{comentario_id}")
    assert del_admin_resp.status_code == 200
    assert del_admin_resp.json() == {"detail": "Comentário removido"}

    # 4. Criar novo comentário do Usuário 1 e ele mesmo deletar -> 200 OK
    app.dependency_overrides[current_user] = lambda: {
        "id": 1,
        "nome": "Usuario Um",
        "email": "user1@teste.com",
        "role": "houston-temos-acesso",
        "permissions": ["criar:comentarios", "apagar:comentario-proprio", "listar:comentarios"],
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


def test_listar_comentarios_exibe_publicacoes_de_outros_usuarios():
    app, TestingSessionLocal, current_user, TestClient = setup_catalogo_app()
    client = TestClient(app)

    app.dependency_overrides[current_user] = lambda: {
        "id": 1,
        "nome": "Autor",
        "email": "autor@teste.com",
        "role": "houston-temos-acesso",
        "permissions": ["listar:comentarios", "criar:comentarios"],
    }
    criado = client.post(
        "/api/comentarios",
        json={"tmdb_movie_id": 550, "texto": "Comentário público"},
    )
    assert criado.status_code == 201

    app.dependency_overrides[current_user] = lambda: {
        "id": 2,
        "nome": "Leitor",
        "email": "leitor@teste.com",
        "role": "amigo-do-wilson",
        "permissions": ["listar:comentarios"],
    }

    todos = client.get("/api/comentarios")
    assert todos.status_code == 200
    assert [comentario["id"] for comentario in todos.json()] == [criado.json()["id"]]

    por_filme = client.get("/api/comentarios/550")
    assert por_filme.status_code == 200
    assert [comentario["id"] for comentario in por_filme.json()] == [criado.json()["id"]]


# ── Auditoria (log-service), /api/logs, logout, health e métricas ─────────────

def _usuario(uid, role, permissions):
    return {"id": uid, "nome": f"User {uid}", "email": f"u{uid}@teste.com", "role": role, "permissions": permissions}


def _capturar_eventos(monkeypatch):
    """Troca o cliente do log-service por um coletor em memória (chamar após setup_catalogo_app)."""
    from app.clients import log_client

    eventos = []

    async def fake_registrar(acao, request=None, usuario_id=None, recurso=None, detalhes=None):
        eventos.append({"acao": acao, "usuario_id": usuario_id, "recurso": recurso, "detalhes": detalhes})

    monkeypatch.setattr(log_client, "registrar", fake_registrar)
    return eventos


def _mock_log_service(monkeypatch, handler):
    import httpx

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.routes.logs.httpx.AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )


def test_health_e_metrics_do_catalogo():
    app, _, _, TestClient = setup_catalogo_app()
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "db": "up"}

    client.get("/api/docs")
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
    assert "http_request_duration_seconds" in metrics.text


def test_health_retorna_503_quando_banco_cai(monkeypatch):
    app, _, _, TestClient = setup_catalogo_app()
    import app.main as main_mod

    class BancoFora:
        def connect(self):
            raise RuntimeError("banco indisponível")

    monkeypatch.setattr(main_mod, "engine", BancoFora())
    resp = TestClient(app).get("/health")
    assert resp.status_code == 503
    assert resp.json()["status"] == "unhealthy"


def test_api_logs_usuario_comum_recebe_403_e_gera_acesso_negado(monkeypatch):
    app, _, current_user, TestClient = setup_catalogo_app()
    eventos = _capturar_eventos(monkeypatch)
    client = TestClient(app)

    app.dependency_overrides[current_user] = lambda: _usuario(
        7, "houston-temos-acesso", ["listar:favoritos", "criar:comentarios"]
    )

    resp = client.get("/api/logs")
    assert resp.status_code == 403
    assert eventos == [
        {"acao": "acesso_negado", "usuario_id": 7, "recurso": "visualizar:logs", "detalhes": "GET /api/logs"}
    ]


def test_api_logs_admin_lista_eventos_do_log_service(monkeypatch):
    import httpx

    app, _, current_user, TestClient = setup_catalogo_app()
    chamadas = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        return httpx.Response(200, json=[{"id": "2-0", "acao": "logout"}, {"id": "1-0", "acao": "login"}])

    _mock_log_service(monkeypatch, handler)
    app.dependency_overrides[current_user] = lambda: _usuario(1, "admin", ["visualizar:logs"])

    resp = TestClient(app).get("/api/logs?limit=20")
    assert resp.status_code == 200
    assert [e["acao"] for e in resp.json()] == ["logout", "login"]
    assert chamadas[0].url.params["limit"] == "20"
    assert "x-internal-token" in chamadas[0].headers


def test_api_logs_retorna_503_se_log_service_estiver_fora(monkeypatch):
    import httpx

    app, _, current_user, TestClient = setup_catalogo_app()

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sem rota", request=request)

    _mock_log_service(monkeypatch, handler)
    app.dependency_overrides[current_user] = lambda: _usuario(1, "admin", ["administrar:sistema"])

    resp = TestClient(app).get("/api/logs")
    assert resp.status_code == 503


def test_favoritar_e_comentar_emitem_eventos(monkeypatch):
    app, _, current_user, TestClient = setup_catalogo_app()
    eventos = _capturar_eventos(monkeypatch)
    client = TestClient(app)
    app.dependency_overrides[current_user] = lambda: _usuario(
        3, "houston-temos-acesso", ["adicionar:favoritos", "criar:comentarios", "apagar:comentario-proprio"]
    )

    assert client.post(
        "/api/favoritos", json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "poster_path": "/fg.jpg"}
    ).status_code == 201
    com = client.post("/api/comentarios", json={"tmdb_movie_id": 13, "texto": "Clássico"})
    assert com.status_code == 201
    assert client.delete(f"/api/comentarios/{com.json()['id']}").status_code == 200

    assert [(e["acao"], e["usuario_id"]) for e in eventos] == [
        ("favoritar", 3),
        ("comentar", 3),
        ("apagar_comentario", 3),
    ]
    assert eventos[0]["recurso"] == "filme:13"
    assert eventos[2]["detalhes"] == "autor"


def test_apagar_comentario_de_outro_registra_moderacao_e_negacao(monkeypatch):
    app, _, current_user, TestClient = setup_catalogo_app()
    eventos = _capturar_eventos(monkeypatch)
    client = TestClient(app)

    app.dependency_overrides[current_user] = lambda: _usuario(1, "houston-temos-acesso", ["criar:comentarios"])
    cid = client.post("/api/comentarios", json={"tmdb_movie_id": 5, "texto": "meu"}).json()["id"]

    # Outro usuário comum tenta apagar: 403 + acesso_negado
    app.dependency_overrides[current_user] = lambda: _usuario(2, "houston-temos-acesso", ["apagar:comentario-proprio"])
    assert client.delete(f"/api/comentarios/{cid}").status_code == 403
    assert eventos[-1]["acao"] == "acesso_negado"
    assert eventos[-1]["usuario_id"] == 2
    assert eventos[-1]["recurso"] == f"comentario:{cid}"

    # Moderador apaga: apagar_comentario com detalhe "moderacao"
    app.dependency_overrides[current_user] = lambda: _usuario(9, "admin", ["apagar:comentario-de-outro"])
    assert client.delete(f"/api/comentarios/{cid}").status_code == 200
    assert eventos[-1]["acao"] == "apagar_comentario"
    assert eventos[-1]["detalhes"] == "moderacao"


def test_login_e_login_falhou_geram_eventos(monkeypatch):
    from fastapi import HTTPException

    app, _, _, TestClient = setup_catalogo_app()
    eventos = _capturar_eventos(monkeypatch)
    client = TestClient(app)

    async def login_ok(method, path, **kw):
        return {"access_token": "t", "token_type": "bearer", "user": {"id": 42, "nome": "A", "email": "a@a.com"}}

    monkeypatch.setattr("app.routes.auth.forward_request", login_ok)
    assert client.post("/api/auth/login", data={"username": "a@a.com", "password": "x"}).status_code == 200
    assert eventos[-1]["acao"] == "login"
    assert eventos[-1]["usuario_id"] == 42

    async def login_401(method, path, **kw):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    monkeypatch.setattr("app.routes.auth.forward_request", login_401)
    assert client.post("/api/auth/login", data={"username": "b@b.com", "password": "x"}).status_code == 401
    assert eventos[-1]["acao"] == "login_falhou"
    assert eventos[-1]["usuario_id"] is None
    assert eventos[-1]["detalhes"] == "email:b@b.com"


def test_logout_exige_jwt_e_registra_evento(monkeypatch):
    app, _, current_user, TestClient = setup_catalogo_app()
    eventos = _capturar_eventos(monkeypatch)
    client = TestClient(app)

    assert client.post("/api/auth/logout").status_code == 401
    assert eventos == []

    app.dependency_overrides[current_user] = lambda: _usuario(5, "admin", ["administrar:sistema"])
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 204
    assert eventos == [{"acao": "logout", "usuario_id": 5, "recurso": None, "detalhes": None}]


def test_cliente_de_log_nunca_levanta_excecao_com_log_service_fora():
    import asyncio

    setup_catalogo_app()
    from app.clients import log_client
    from app.core.config import settings

    settings.LOG_SERVICE_URL = "http://127.0.0.1:9"  # porta fechada
    asyncio.run(log_client.registrar("teste"))  # não deve levantar
