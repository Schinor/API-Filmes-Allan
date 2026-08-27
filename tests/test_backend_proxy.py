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


def test_catalogo_app_structure():
    for mod in list(sys.modules.keys()):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]

    sys.path.insert(0, os.path.abspath("backend"))

    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import Base, get_db
    from app.core.security import CurrentUser, get_current_user

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
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=1, nome="Allan Teste", email="allan@teste.com", role="usuario"
    )

    client = TestClient(app)

    response = client.get("/api/docs")
    assert response.status_code == 200

    fav_list = client.get("/api/favoritos")
    assert fav_list.status_code == 200
    assert isinstance(fav_list.json(), list)

    com_list = client.get("/api/comentarios")
    assert com_list.status_code == 200
    assert isinstance(com_list.json(), list)
