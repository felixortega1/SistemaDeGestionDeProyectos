import datetime

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.backlog import services as backlog
from apps.projects import services as projects
from apps.projects.models import ProjectMember
from apps.sprints import services as sprints


class CsrfClient(Client):
    """Cliente con comprobación CSRF activa que añade el token en cada POST."""

    def __init__(self, **kw):
        super().__init__(enforce_csrf_checks=True, **kw)

    def post(self, path, data=None, **extra):
        if "HTTP_X_CSRFTOKEN" not in extra and not extra.pop("no_csrf", False):
            self.get("/accounts/login/")
            token = self.cookies.get("csrftoken")
            if token:
                extra["HTTP_X_CSRFTOKEN"] = token.value
        extra.pop("no_csrf", None)
        return super().post(path, data or {}, **extra)


@pytest.fixture
def make_user(db):
    counter = {"n": 0}

    def _make(email=None, **kw):
        counter["n"] += 1
        email = email or f"user{counter['n']}@example.com"
        return get_user_model().objects.create_user(email, "s3cret-pass-123", name=email.split("@")[0], **kw)

    return _make


@pytest.fixture
def client_for():
    def _client(user):
        c = CsrfClient()
        c.force_login(user)
        return c

    return _client


@pytest.fixture
def po(make_user):
    return make_user("po@example.com")


@pytest.fixture
def project(po):
    return projects.create_project(po, "Proyecto A", "desc")


@pytest.fixture
def add_member(make_user):
    def _add(project, role, user=None):
        user = user or make_user()
        ProjectMember.objects.create(project=project, user=user, role=role)
        return user

    return _add


@pytest.fixture
def sm(project, add_member):
    return add_member(project, ProjectMember.SCRUM_MASTER)


@pytest.fixture
def dev(project, add_member):
    return add_member(project, ProjectMember.DEVELOPER)


@pytest.fixture
def make_task(project):
    def _make(title="Tarea", proj=None, **kw):
        return backlog.create_task(proj or project, title=title, **kw)

    return _make


@pytest.fixture
def make_story(project):
    def _make(title="Historia", proj=None, **kw):
        return backlog.create_story(proj or project, title=title, **kw)

    return _make


@pytest.fixture
def today():
    return datetime.date.today()


@pytest.fixture
def active_sprint(project, make_task, today):
    """Crea un sprint activo con n tareas (todas en la primera columna)."""

    def _make(n=3, proj=None, **task_kw):
        proj = proj or project
        sprint = sprints.create_sprint(
            proj, "Sprint 1", start_date=today - datetime.timedelta(days=7), end_date=today - datetime.timedelta(days=1)
        )
        tasks = [make_task(f"T{i}", proj=proj, **task_kw) for i in range(n)]
        for t in tasks:
            backlog.assign_sprint(t, sprint)
        sprints.start_sprint(sprint)
        sprint.refresh_from_db()
        for t in tasks:
            t.refresh_from_db()
        return sprint, tasks

    return _make


@pytest.fixture
def columns(project):
    return {c.name: c for c in project.columns.all()}
