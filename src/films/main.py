"""Точка сборки и запуска FastAPI-приложения."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from films.api.router import main_api_router
from films.config import settings
from films.database import engine
from films.exceptions.handler import register_exception_handlers
from films.mongo import close_mongo, connect_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализировать и освободить подключения приложения."""

    mongo_connection = await connect_mongo()
    app.state.mongo_db = (
        mongo_connection.database if mongo_connection is not None else None
    )

    try:
        yield
    finally:
        close_mongo(mongo_connection)
        await engine.dispose()


app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(main_api_router)

register_exception_handlers(app)
