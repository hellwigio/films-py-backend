class AppError(Exception):
    pass


class EntityNotFoundError(AppError):
    pass


class InvalidSearchError(AppError):
    pass


class ServiceUnavailableError(AppError):
    pass
