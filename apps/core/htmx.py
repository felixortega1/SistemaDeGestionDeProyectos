from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def htmx_unauthorized(request):
    response = HttpResponse(status=401)
    response["HX-Redirect"] = "/accounts/login/"
    return response


def fragment_or_redirect(request, template, context, redirect_to, status=200):
    """Devuelve el fragmento si la petición es HTMX; si no, redirige a la página completa."""
    if is_htmx(request):
        return render(request, template, context, status=status)
    return redirect(redirect_to)


def redirect_back(request, default):
    """Redirige a `next` (si es seguro) o a `default`."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect(default)
