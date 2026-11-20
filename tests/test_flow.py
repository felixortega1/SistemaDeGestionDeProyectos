import datetime

import pytest

from apps.backlog import services as backlog
from apps.backlog.models import Comment, Story, Task
from apps.core.exceptions import Conflict, Forbidden, Unprocessable
from apps.projects import services as projects

D = datetime.date


def new_project(user, name="P", company_name="Acme"):
    return projects.create_project(
        user,
        name,
        company_name=company_name,
        start_date=D(2026, 1, 1),
        end_date=D(2026, 6, 30),
        objectives="Uno\nDos",
    )


# ------------------------------------------------ empresas y proyectos
def test_user_sees_only_companies_with_their_projects(po, make_user):
    other = make_user()
    mine = new_project(po, "Mio", "Acme")
    new_project(other, "Ajeno", "Otra empresa")
    assert [c.name for c in projects.companies_for(po)] == ["Acme"]
    assert mine.company.name == "Acme"


def test_home_lists_companies_and_company_page_lists_projects(po, client_for):
    p1 = new_project(po, "Proyecto uno", "Acme")
    new_project(po, "Proyecto dos", "Beta")
    c = client_for(po)
    home = c.get("/")
    assert home.status_code == 200 and b"Acme" in home.content and b"Beta" in home.content
    page = c.get(f"/companies/{p1.company_id}/")
    assert b"Proyecto uno" in page.content and b"Proyecto dos" not in page.content
    assert b"01/01/2026" in page.content and b"30/06/2026" in page.content  # fechas de inicio y fin
    assert b"Uno" in page.content and b"Dos" in page.content  # objetivos


def test_company_of_others_is_404(po, make_user, client_for):
    p = new_project(make_user(), "Ajeno", "Secreta")
    assert client_for(po).get(f"/companies/{p.company_id}/").status_code == 404


def test_objectives_limit_and_dates(po):
    with pytest.raises(Unprocessable):
        projects.create_project(po, "X", objectives="a\nb\nc\nd")
    with pytest.raises(Unprocessable):
        projects.create_project(po, "X", start_date=D(2026, 5, 1), end_date=D(2026, 4, 1))
    p = projects.create_project(po, "X", objectives="a\n\n  b  \n")
    assert p.objective_list == ["a", "b"]


def test_project_form_requires_dates_objectives_and_company(po, client_for):
    c = client_for(po)
    assert c.post("/projects/new/", {"name": "Sin datos"}).status_code == 422
    data = {
        "company_name": "Nueva SA",
        "name": "Completo",
        "start_date": "2026-02-01",
        "end_date": "2026-03-01",
        "objectives": "Meta 1",
    }
    assert c.post("/projects/new/", data).status_code == 302
    assert projects.companies_for(po).filter(name="Nueva SA").exists()


def test_cannot_reuse_a_company_of_others(po, make_user):
    foreign = new_project(make_user(), "Ajeno", "Secreta").company
    with pytest.raises(Unprocessable):
        projects.create_project(po, "X", company=foreign)


def test_edit_project_po_only(project, po, dev, client_for):
    data = {
        "name": "Nuevo nombre",
        "company_name": "Otra",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "objectives": "Meta",
    }
    assert client_for(dev).post(f"/projects/{project.pk}/edit/", data).status_code == 403
    assert client_for(po).post(f"/projects/{project.pk}/edit/", data).status_code == 302
    project.refresh_from_db()
    assert project.name == "Nuevo nombre" and project.company.name == "Otra" and project.objective_list == ["Meta"]


# ------------------------------------------------ historias, actividades y sprints
def test_story_pages_and_task_creation(project, po, client_for):
    c = client_for(po)
    r = c.post(f"/projects/{project.pk}/stories/new/", {"title": "El usuario debe pagar con tarjeta", "stakeholder": "Ventas"})
    assert r.status_code == 302
    story = Story.objects.get()
    assert r.url == f"/stories/{story.pk}/"
    assert story.stakeholder == "Ventas"
    assert b"pagar con tarjeta" in c.get(f"/projects/{project.pk}/stories/").content
    assert c.post(f"/stories/{story.pk}/tasks/new/", {"title": "Integrar pasarela"}).status_code == 302
    task = Task.objects.get()
    assert task.story_id == story.pk
    assert b"Integrar pasarela" in c.get(f"/stories/{story.pk}/").content
    assert c.get(f"/projects/{project.pk}/").url == f"/projects/{project.pk}/stories/"


def test_assign_story_to_sprint(project, make_task, make_story, today):
    from apps.sprints import services as sprint_services

    story = make_story("hist")
    a, b = make_task("a", story=story), make_task("b", story=story)
    sprint = sprint_services.create_sprint(project, "S", start_date=today, end_date=today)
    assert len(backlog.assign_story_to_sprint(story, sprint)) == 2
    a.refresh_from_db()
    b.refresh_from_db()
    assert a.sprint_id == b.sprint_id == sprint.pk and a.column_id
    with pytest.raises(Unprocessable):
        backlog.assign_story_to_sprint(story, sprint)  # ya no queda nada pendiente


def test_assign_story_is_all_or_nothing(project, make_task, make_story, today, columns):
    from apps.sprints import services as sprint_services

    story = make_story("hist")
    a, b = make_task("a", story=story), make_task("b", story=story)
    sprint = sprint_services.create_sprint(project, "S", start_date=today, end_date=today)
    sprint_services.start_sprint(sprint)
    first = columns["Por hacer"]
    first.wip_limit = 1
    first.save()
    with pytest.raises(Conflict):
        backlog.assign_story_to_sprint(story, sprint)
    a.refresh_from_db()
    b.refresh_from_db()
    assert a.sprint_id is None and b.sprint_id is None  # se revirtió todo


def test_assign_story_via_view_roles(project, sm, dev, make_task, make_story, today, client_for):
    from apps.sprints import services as sprint_services

    story = make_story("hist")
    make_task("a", story=story)
    sprint = sprint_services.create_sprint(project, "S", start_date=today, end_date=today)
    url = f"/stories/{story.pk}/assign-sprint/"
    assert client_for(dev).post(url, {"sprint_id": sprint.pk}).status_code == 403
    assert client_for(sm).post(url, {"sprint_id": sprint.pk}).status_code == 302


# ------------------------------------------------ comentarios
def test_members_can_comment_on_story_and_task(project, po, dev, make_task, make_story, client_for):
    story = make_story("hist")
    task = make_task("act", story=story)
    r = client_for(po).post(f"/stories/{story.pk}/comments/add/", {"body": "Necesito más detalle"})
    assert r.status_code == 302
    r = client_for(dev).post(f"/tasks/{task.pk}/comments/add/", {"body": "Necesito más detalle"})
    assert r.status_code == 302
    assert Comment.objects.count() == 2
    assert Comment.objects.filter(story=story, task__isnull=True).count() == 1
    assert Comment.objects.filter(task=task, story__isnull=True).count() == 1
    assert b"Necesito" in client_for(po).get(f"/stories/{story.pk}/").content
    assert b"Necesito" in client_for(po).get(f"/tasks/{task.pk}/").content


def test_empty_comment_is_422_and_outsider_gets_404(project, po, make_user, make_task, client_for):
    t = make_task("act")
    assert client_for(po).post(f"/tasks/{t.pk}/comments/add/", {"body": "   "}).status_code == 422
    assert client_for(make_user()).post(f"/tasks/{t.pk}/comments/add/", {"body": "hola"}).status_code == 404
    with pytest.raises(Forbidden):
        backlog.add_comment(t, make_user(), "hola")


def test_delete_comment_only_author_or_po(project, dev, add_member, make_task, client_for, po):
    t = make_task("act")
    other = add_member(project, "developer")
    comment = backlog.add_comment(t, dev, "mío")
    assert client_for(other).post(f"/comments/{comment.pk}/delete/").status_code == 403
    assert client_for(dev).post(f"/comments/{comment.pk}/delete/").status_code == 302
    second = backlog.add_comment(t, dev, "otro")
    assert client_for(po).post(f"/comments/{second.pk}/delete/").status_code == 302
    assert Comment.objects.count() == 0


def test_comments_are_removed_with_their_task(project, po, make_task):
    t = make_task("act")
    backlog.add_comment(t, po, "x")
    backlog.delete_task(t)
    assert Comment.objects.count() == 0


# ------------------------------------------------ roles que crean historias
@pytest.fixture
def pm(project, add_member):
    return add_member(project, "project_manager")


@pytest.mark.parametrize("who", ["po", "pm", "sm"])
def test_po_pm_and_sm_can_create_stories_and_activities(project, po, pm, sm, who, client_for):
    user = {"po": po, "pm": pm, "sm": sm}[who]
    c = client_for(user)
    r = c.post(f"/projects/{project.pk}/stories/new/", {"title": f"Historia de {who}", "stakeholder": "Cliente"})
    assert r.status_code == 302
    story = Story.objects.get(title=f"Historia de {who}")
    assert c.post(f"/stories/{story.pk}/tasks/new/", {"title": "Una tarea"}).status_code == 302
    assert story.tasks.count() == 1
    page = c.get(f"/projects/{project.pk}/stories/").content
    assert b"Nueva historia" in page and b"Las historias las crean" not in page


def test_developer_cannot_create_stories_and_sees_notice(project, dev, client_for):
    c = client_for(dev)
    assert c.post(f"/projects/{project.pk}/stories/new/", {"title": "No debería"}).status_code == 403
    story = backlog.create_story(project, title="Existente")
    assert c.post(f"/stories/{story.pk}/tasks/new/", {"title": "No"}).status_code == 403
    page = c.get(f"/projects/{project.pk}/stories/").content
    assert b"Las historias las crean" in page and b"Nueva historia" not in page
    assert not Story.objects.filter(title="No debería").exists()


def test_story_roles_only_apply_inside_their_own_project(project, po, pm, make_user, client_for):
    other_owner = make_user()
    other = projects.create_project(other_owner, "Otro proyecto")
    # pm es Project Manager en `project`, pero ni siquiera es miembro de `other`
    assert client_for(pm).post(f"/projects/{other.pk}/stories/new/", {"title": "X"}).status_code == 404


def test_project_manager_has_management_permissions(project, pm, client_for):
    c = client_for(pm)
    assert c.post(f"/projects/{project.pk}/sprints/new/", {"name": "S1"}).status_code == 302
    assert c.get(f"/projects/{project.pk}/columns/").status_code == 200
    data = {"name": "Marketing", "budget_amount": "100", "currency": "USD"}
    assert c.post(f"/projects/{project.pk}/departments/new/", data).status_code == 302
    assert c.post(f"/projects/{project.pk}/members/add/", {"email": "x@example.com", "role": "developer"}).status_code == 403


def test_po_can_assign_project_manager_role_and_transfer_to_it(project, po, dev, client_for):
    c = client_for(po)
    assert c.post(f"/projects/{project.pk}/members/{dev.pk}/role/", {"role": "project_manager"}).status_code == 302
    assert project.members.get(user=dev).role == "project_manager"
    r = c.post(f"/projects/{project.pk}/transfer-po/", {"user_id": dev.pk, "outgoing_role": "project_manager"})
    assert r.status_code == 302
    assert project.members.get(user=po).role == "project_manager"
    assert project.members.get(user=dev).role == "product_owner"
