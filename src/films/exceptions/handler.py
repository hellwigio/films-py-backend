"""Преобразование исключений приложения в единые JSON-ответы."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from films.exceptions.base import (
    AppError,
    EntityNotFoundError,
    InvalidSearchError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)

ERROR_MAP = {
    EntityNotFoundError: {
        "status_code": 404,
        "error_type": "Not Found",
    },
    InvalidSearchError: {
        "status_code": 422,
        "error_type": "Invalid search parameters",
    },
    ServiceUnavailableError: {
        "status_code": 503,
        "error_type": "Service unavailable",
    },
}

DEFAULT_ERROR = {
    "status_code": 500,
    "error_type": "Internal Server Error",
}


async def app_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Преобразовать ожидаемую ошибку приложения в JSON-ответ."""

    if not isinstance(exc, AppError):
        raise exc

    error = DEFAULT_ERROR

    for cls in type(exc).__mro__:
        if cls in ERROR_MAP:
            error = ERROR_MAP[cls]
            break

    return JSONResponse(
        status_code=error["status_code"],
        content={"error": error["error_type"], "message": exc.message},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать ожидаемый и резервный обработчики ошибок."""

    app.add_exception_handler(AppError, app_exception_handler)

    async def unexpected_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        """Скрыть детали непредвиденной ошибки и записать traceback в лог."""

        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": (
                    "Системная ошибка. Повторите запрос позже или проверьте "
                    "доступность MySQL и MongoDB."
                ),
            },
        )

    app.add_exception_handler(Exception, unexpected_exception_handler)
