class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class DomainRuleError(AppException):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code=status_code)
