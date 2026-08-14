"""Ошибки поиска и доступа к его истории."""

from films.exceptions.base import InvalidSearchError, ServiceUnavailableError


class SearchParametersError(InvalidSearchError):
    """Значения фильтров не поддерживаются текущим каталогом."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class SearchHistoryUnavailableError(ServiceUnavailableError):
    """Статистика поиска недоступна из-за состояния MongoDB."""

    def __init__(self):
        self.message = (
            "История поиска временно недоступна. Проверьте MongoDB и повторите запрос."
        )
        super().__init__(self.message)
