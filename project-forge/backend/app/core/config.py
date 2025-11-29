"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "your_db"
    DB_USER: str = "your_user"
    DB_PASSWORD: str = "your_pass"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Application
    APP_ENV: str = "dev"
    APP_LOG_FILE: str = str(Path(__file__).parent.parent.parent.parent / "logs" / "app.log")
    APP_PORT: int = 8000
    TZ_DB_SOURCE: str = "America/Chicago"
    TZ_TRADING: str = "America/New_York"
    
    # API Security
    API_KEY: Optional[str] = "dev-key-change-in-production"
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def database_url_sync(self) -> str:
        """Construct synchronous PostgreSQL database URL for Alembic."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        # Look for .env in project root (2 levels up from backend/app/core/)
        # Use absolute path to ensure it works regardless of CWD
        _project_root = Path(__file__).parent.parent.parent.parent.resolve()
        _env_file = _project_root / ".env"
        env_file = str(_env_file)
        case_sensitive = True


# Global settings instance
settings = Settings()

