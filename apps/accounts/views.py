from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegisterForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            login(request, form.save())
            return redirect("/")
        return render(request, "accounts/register.html", {"form": form}, status=422)
    return render(request, "accounts/register.html", {"form": RegisterForm()})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login(request, form.user)
            nxt = request.GET.get("next", "")
            from django.utils.http import url_has_allowed_host_and_scheme

            if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                return redirect(nxt)
            return redirect("/")
        return render(request, "accounts/login.html", {"form": form}, status=422)
    return render(request, "accounts/login.html", {"form": LoginForm()})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")
