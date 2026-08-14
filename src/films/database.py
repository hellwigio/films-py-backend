"""Настройка асинхронного SQLAlchemy и зависимость сессии."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from films.config import settings

engine = create_async_engine(settings.DB_URL, echo=settings.DEBUG)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс ORM-моделей приложения."""


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Предоставить отдельную SQLAlchemy-сессию на время запроса."""

    async with async_session_maker() as session:
        yield session
