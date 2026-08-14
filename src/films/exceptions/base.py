"""Базовая иерархия ожидаемых ошибок приложения."""


class AppError(Exception):
    """Базовая ошибка, которую можно безопасно вернуть клиенту."""

    message: str


class EntityNotFoundError(AppError):
    """Запрошенная сущность не найдена."""


class InvalidSearchError(AppError):
    """Параметры поиска противоречат правилам приложения."""


class ServiceUnavailableError(AppError):
    """Вспомогательный сервис временно недоступен."""
