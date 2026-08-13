from src.exceptions.base import InvalidSearchError, ServiceUnavailableError


class SearchParametersError(InvalidSearchError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class SearchHistoryUnavailableError(ServiceUnavailableError):
    def __init__(self):
        self.message = (
            "История поиска временно недоступна. Проверьте MongoDB и повторите запрос."
        )
        super().__init__(self.message)
