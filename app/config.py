"""Configuration settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Project Management Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    ENVIRONMENT: str = "development"

    # Database — required; set via DATABASE_URL env var
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_asyncpg(cls, v: str) -> str:
        return v.replace("postgresql://", "postgresql+asyncpg://")

    # JWT Authentication — RS256 public-key verification only.
    # Tokens are signed by user-management with its private key.
    # This service only needs the public key to verify; it cannot issue tokens.
    JWT_PUBLIC_KEY_B64: str
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def jwt_public_key(self) -> str:
        import base64

        return base64.b64decode(self.JWT_PUBLIC_KEY_B64).decode("utf-8")

    # Redis
    REDIS_URL: str = "redis://redis:6379/4"

    # Internal service URLs (all on :8080 inside Docker network)
    USER_SERVICE_URL: str = "http://user-management:8080"
    CRM_SERVICE_URL: str = "http://crm:8080"
    PROCUREMENT_SERVICE_URL: str = "http://procurement-inventory:8080"
    FINANCE_SERVICE_URL: str = "http://finance-accounting:8080"
    NOTIFICATION_SERVICE_URL: str = "http://user-management:8080/notifications"

    # Currency
    DEFAULT_CURRENCY: str = "GHS"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list:
        if isinstance(self.CORS_ORIGINS, str):
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return self.CORS_ORIGINS

    # Email - Mailgun Configuration
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    MAILGUN_FROM_EMAIL: str = "noreply@imperialhomesghana.com"
    MAILGUN_FROM_NAME: str = "OneImperial ERP"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
