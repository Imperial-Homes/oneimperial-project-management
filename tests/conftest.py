"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_project_mgmt_db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Create test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_rsa_keypair():
    """Generate an ephemeral RSA key pair used only during the test session."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import base64

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
    from jose import jwt
    from app.config import settings

    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY_B64", test_rsa_keypair["public_b64"])

    user_id = str(uuid4())
    token_data = {"sub": user_id}
    token = jwt.encode(token_data, test_rsa_keypair["private_pem"], algorithm="RS256")
    return token


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Generate authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}
