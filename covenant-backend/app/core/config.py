from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Covenant — AI Legal Copilot Platform"
    ENVIRONMENT: str = "development"

    # PostgreSQL — matches the local instance you already have installed.
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/covenant"

    # Auth
    SECRET_KEY: str = "change-me-in-.env-before-any-real-deployment"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    # CORS — the Vite dev server default port
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b"

    # Uploads
    MAX_UPLOAD_MB: int = 25
    UPLOAD_DIR: str = "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
