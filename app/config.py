"""Configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Project Management Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://projectmgmt:projectmgmt@localhost:5432/project_mgmt_db"
    
    # JWT Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/4"
    
    # External Services
    USER_SERVICE_URL: str = "http://localhost:8001"
    CRM_SERVICE_URL: str = "http://localhost:8004"
    PROCUREMENT_SERVICE_URL: str = "http://localhost:8006"
    FINANCE_SERVICE_URL: str = "http://localhost:8003"
    
    # Currency
    DEFAULT_CURRENCY: str = "GHS"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://api.imperialhomesghana.com",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
