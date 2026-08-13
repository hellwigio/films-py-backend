from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    APP_TITLE: str = "Films API"
    APP_VERSION: str = "0.0.1"
    DEBUG: bool = False

    DB_URL: str = ""
    MONGO_URL: str = ""
    SEARCH_QUERIES_COLLECTION: str = "final_project_ichub_dmitriy_hellwig"
    SEARCH_STATISTICS_LIMIT: int = 5
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("DB_URL")
    @classmethod
    def validate_db_url(cls, value: str) -> str:
        if not value:
            raise ValueError("DB_URL must be set")

        try:
            make_url(value)
        except ArgumentError as exc:
            raise ValueError("DB_URL must be a valid SQLAlchemy database URL") from exc

        return value

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Синглтон настроек
settings = Settings()
