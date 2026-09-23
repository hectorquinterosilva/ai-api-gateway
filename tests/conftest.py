"""
Configuración de pytest: base de datos SQLite en memoria y cliente HTTP.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importar modelos para que se registren en Base.metadata
import app.models  # noqa: F401

from app.db.base import Base
from app.db.session import get_db
from app.main import app


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """
    Crea una DB SQLite en memoria por test, con todas las tablas.
    StaticPool mantiene una sola conexión para que :memory: persista.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    """
    Cliente HTTP con la dependencia get_db sobreescrita por la sesión de test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
