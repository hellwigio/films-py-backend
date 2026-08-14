import pytest
from pydantic import ValidationError

from films.config import Settings


def test_settings_requires_db_url() -> None:
    with pytest.raises(ValidationError, match="DB_URL must be set"):
        Settings(DB_URL="")


def test_settings_rejects_invalid_db_url() -> None:
    with pytest.raises(
        ValidationError, match="DB_URL must be a valid SQLAlchemy database URL"
    ):
        Settings(DB_URL="not a database url")


def test_settings_accepts_sqlalchemy_db_url() -> None:
    settings = Settings(DB_URL="mysql+asyncmy://user:pass@localhost:3306/sakila")

    assert settings.DB_URL == "mysql+asyncmy://user:pass@localhost:3306/sakila"
