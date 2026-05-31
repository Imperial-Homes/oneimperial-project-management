"""Pytest configuration and fixtures."""

import base64
import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import jwt
import pytest
from app.database import Base, get_db
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test database URL — reads from env so tests work in CI and local Docker
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_project_mgmt_db")


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_rsa_keypair():
    """Generate an ephemeral RSA key pair used only during the test session."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return {
        "private_pem": private_pem.decode("utf-8"),
        "public_b64": base64.b64encode(public_pem).decode("utf-8"),
    }


@pytest.fixture
def auth_token(test_rsa_keypair, monkeypatch) -> str:
    """Generate a test JWT token signed with an ephemeral RSA key (RS256)."""
    from app.config import settings

    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY_B64", test_rsa_keypair["public_b64"])

    user_id = str(uuid4())
    token_data = {"sub": user_id}
    return jwt.encode(token_data, test_rsa_keypair["private_pem"], algorithm="RS256")


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Generate authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}
