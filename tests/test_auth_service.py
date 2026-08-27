import os
import sys

# Define variáveis de ambiente para a suíte de testes
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_12345678901234567890"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"
os.environ["RESET_TOKEN_EXPIRE_MINUTES"] = "30"

# Adiciona caminhos
sys.path.insert(0, os.path.abspath("auth-service"))

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models.usuario import Usuario
from app.models.reset_token import ResetToken
from app.main import app

# Banco de dados em memória exclusivo para a suite de testes automatizados
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "auth-service"


def test_cadastro_e_login_usuario():
    # 1. Cadastro
    cad_resp = client.post(
        "/cadastro",
        json={"nome": "Allan Schinor", "email": "allan@exemplo.com", "senha": "senhaSegura123"},
    )
    assert cad_resp.status_code == 201
    cad_data = cad_resp.json()
    assert cad_data["nome"] == "Allan Schinor"
    assert cad_data["email"] == "allan@exemplo.com"
    assert cad_data["role"] == "usuario"
    user_id = cad_data["id"]

    # Cadastro duplicado deve falhar
    dup_resp = client.post(
        "/cadastro",
        json={"nome": "Allan 2", "email": "allan@exemplo.com", "senha": "senhaSegura123"},
    )
    assert dup_resp.status_code == 400

    # 2. Login
    login_resp = client.post(
        "/login",
        data={"username": "allan@exemplo.com", "password": "senhaSegura123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 3. /me
    me_resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "allan@exemplo.com"

    # 4. /users/{id}/role
    role_resp = client.get(f"/users/{user_id}/role")
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "usuario"


def test_roles_usuario_e_admin():
    # Cadastro de admin
    admin_resp = client.post(
        "/cadastro",
        json={"nome": "Siriani Admin", "email": "siriani@exemplo.com", "senha": "adminSecret123", "role": "admin"},
    )
    assert admin_resp.status_code == 201
    admin_id = admin_resp.json()["id"]

    role_resp = client.get(f"/users/{admin_id}/role")
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "admin"


def test_fluxo_completo_esqueci_senha_e_redefinicao():
    # 1. Cria usuário
    client.post(
        "/cadastro",
        json={"nome": "Usuario Teste", "email": "recuperar@exemplo.com", "senha": "senhaAntiga123"},
    )

    # 2. Solicita recuperação para e-mail não cadastrado (deve retornar 404)
    fake_resp = client.post("/forgot-password", json={"email": "inexistente@exemplo.com"})
    assert fake_resp.status_code == 404

    # 3. Solicita recuperação para e-mail cadastrado
    forgot_resp = client.post("/forgot-password", json={"email": "recuperar@exemplo.com"})
    assert forgot_resp.status_code == 200
    token = forgot_resp.json()["token"]
    assert token is not None

    # 4. Valida token antes do uso
    val_resp = client.get(f"/validate-reset-token/{token}")
    assert val_resp.status_code == 200
    assert val_resp.json()["valid"] is True
    assert val_resp.json()["email"] == "recuperar@exemplo.com"

    # 5. Redefine a senha com sucesso
    reset_resp = client.post(
        "/reset-password",
        json={"token": token, "nova_senha": "novaSenhaSuperSegura456"},
    )
    assert reset_resp.status_code == 200
    assert "sucesso" in reset_resp.json()["message"].lower()

    # 6. Login com senha antiga deve falhar (401)
    fail_login = client.post(
        "/login",
        data={"username": "recuperar@exemplo.com", "password": "senhaAntiga123"},
    )
    assert fail_login.status_code == 401

    # 7. Login com nova senha deve suceder (200)
    ok_login = client.post(
        "/login",
        data={"username": "recuperar@exemplo.com", "password": "novaSenhaSuperSegura456"},
    )
    assert ok_login.status_code == 200


def test_negativo_reuso_de_token():
    # Cria usuário e token
    client.post(
        "/cadastro",
        json={"nome": "Reuso Teste", "email": "reuso@exemplo.com", "senha": "senhaOriginal123"},
    )
    forgot_resp = client.post("/forgot-password", json={"email": "reuso@exemplo.com"})
    token = forgot_resp.json()["token"]

    # Primeiro uso: OK
    r1 = client.post("/reset-password", json={"token": token, "nova_senha": "novaSenha123"})
    assert r1.status_code == 200

    # Segundo uso (tentativa de reuso): DEVE SER RECUSADO
    r2 = client.post("/reset-password", json={"token": token, "nova_senha": "outraSenha123"})
    assert r2.status_code == 400
    assert "já foi utilizado" in r2.json()["detail"].lower()


def test_negativo_token_expirado():
    db = TestingSessionLocal()
    # Cria usuário
    cad_resp = client.post(
        "/cadastro",
        json={"nome": "Expirado Teste", "email": "expirado@exemplo.com", "senha": "senhaOriginal123"},
    )
    user_id = cad_resp.json()["id"]

    # Cria token diretamente no DB com data de expiração no passado (mais de 30 minutos atrás)
    token_expirado_str = "token_expirado_de_teste_12345"
    db_token = ResetToken(
        token=token_expirado_str,
        usuario_id=user_id,
        criado_em=datetime.utcnow() - timedelta(minutes=45),
        expira_em=datetime.utcnow() - timedelta(minutes=15),
        usado=False,
    )
    db.add(db_token)
    db.commit()
    db.close()

    # Tentativa de validar token expirado
    val_resp = client.get(f"/validate-reset-token/{token_expirado_str}")
    assert val_resp.json()["valid"] is False

    # Tentativa de trocar senha com token expirado: DEVE SER RECUSADA
    reset_resp = client.post(
        "/reset-password",
        json={"token": token_expirado_str, "nova_senha": "novaSenhaExpirada123"},
    )
    assert reset_resp.status_code == 400
    assert "expirou" in reset_resp.json()["detail"].lower()


def test_negativo_token_inexistente():
    reset_resp = client.post(
        "/reset-password",
        json={"token": "token_que_nunca_existiu_999", "nova_senha": "senhaQualquer123"},
    )
    assert reset_resp.status_code == 400
    assert "inválido" in reset_resp.json()["detail"].lower()
