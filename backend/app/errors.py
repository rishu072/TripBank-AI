class AppError(Exception):
    def __init__(self, code: str, message: str = "", status: int = 400):
        self.code = code
        self.message = message or code
        self.status = status
