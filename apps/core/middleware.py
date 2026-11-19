from django.shortcuts import render

from .exceptions import ServiceError


class ServiceExceptionMiddleware:
    """Convierte las excepciones de los servicios en una página de error con su estado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, ServiceError):
            return render(
                request,
                "error.html",
                {"status": exception.status, "message": exception.message},
                status=exception.status,
            )
        return None
