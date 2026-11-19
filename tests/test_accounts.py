import pytest
from django.contrib.sessions.models import Session

from tests.conftest import CsrfClient

PASSWORD = "s3cret-pass-123"


@pytest.mark.django_db
def test_register_login_logout_deletes_session(make_user):
    c = CsrfClient()
    r = c.post("/accounts/register/", {"name": "Ana", "email": "Ana@Example.com", "password1": PASSWORD, "password2": PASSWORD})
    assert r.status_code == 302
    assert Session.objects.count() == 1
    r = c.post("/accounts/logout/")
    assert r.status_code == 302
    assert Session.objects.count() == 0
    r = c.post("/accounts/login/", {"email": "ana@example.com", "password": PASSWORD})
    assert r.status_code == 302


@pytest.mark.django_db
def test_duplicate_email_is_422(make_user):
    make_user("dup@example.com")
    r = CsrfClient().post(
        "/accounts/register/", {"name": "X", "email": "DUP@example.com", "password1": PASSWORD, "password2": PASSWORD}
    )
    assert r.status_code == 422


@pytest.mark.django_db
def test_bad_login(make_user):
    make_user("a@example.com")
    r = CsrfClient().post("/accounts/login/", {"email": "a@example.com", "password": "wrong"})
    assert r.status_code == 422


@pytest.mark.django_db
def test_post_without_csrf_is_403():
    r = CsrfClient().post("/accounts/login/", {"email": "a@example.com", "password": "x"}, no_csrf=True)
    assert r.status_code == 403


@pytest.mark.django_db
def test_redirect_to_login_without_session():
    r = CsrfClient().get("/")
    assert r.status_code == 302 and r.url.startswith("/accounts/login/")


@pytest.mark.django_db
def test_htmx_without_session_gets_401_with_redirect(project):
    r = CsrfClient().get(f"/projects/{project.pk}/board/", HTTP_HX_REQUEST="true")
    assert r.status_code == 401
    assert r["HX-Redirect"] == "/accounts/login/"


@pytest.mark.django_db
def test_password_is_argon2(make_user):
    assert make_user().password.startswith("argon2")
