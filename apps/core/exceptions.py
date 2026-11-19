class ServiceError(Exception):
    status = 500

    def __init__(self, message=""):
        super().__init__(message)
        self.message = message


class Conflict(ServiceError):
    status = 409


class Unprocessable(ServiceError):
    status = 422


class Forbidden(ServiceError):
    status = 403


class NotFound(ServiceError):
    status = 404
