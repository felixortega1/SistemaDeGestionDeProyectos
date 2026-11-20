"""Flujo Scrum: épicas, criterios de aceptación, prioridad, devolver al backlog, métricas y contexto del tablero."""

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.backlog import services
from apps.backlog.models import AcceptanceCriterion, Comment, Epic, Story, Task
from apps.core.exceptions import Conflict, Forbidden, Unprocessable
from apps.projects import services as project_services
from apps.sprints import services as sprint_services

HX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def epic(project):
    return services.create_epic(project, title="Pagos", description="Todo lo de cobros", color="#aa00cc")


@pytest.fixture
def story(make_story, epic):
    return make_story("Historia de pago", epic=epic)


@pytest.fixture
def outsider(make_user):
    return make_user("fuera@example.com")


# ------------------------------------------------ épicas: servicios
def test_epic_crud_and_color_validation(project):
    e = services.create_epic(project, title="  Pagos  ", color="#aa00cc")
    assert e.title == "Pagos" and e.color == "#AA00CC" and e.project_id == project.pk
    services.update_epic(e, title="Cobros", description="d", color="#112233")
    e.refresh_from_db()
    assert (e.title, e.description, e.color) == ("Cobros", "d", "#112233")
    for bad in ("red", "#12345", "#GGGGGG", "112233", ""):
        with pytest.raises(Unprocessable):
            services.create_epic(project, title="X", color=bad)
    with pytest.raises(Unprocessable):
        services.create_epic(project, title="   ")
    assert Epic.objects.get(pk=e.pk).color == "#112233"


def test_story_epic_must_be_of_the_same_project(project, po, make_story, epic):
    story = make_story("hist", epic=epic)
    assert story.epic_id == epic.pk
    other = project_services.create_project(po, "Otro")
    foreign = services.create_epic(other, title="Ajena")
    with pytest.raises(Unprocessable):
        make_story("hist2", epic=foreign)
    services.update_story(story, epic=None)
    story.refresh_from_db()
    assert story.epic_id is None


def test_delete_epic_with_stories_is_conflict(project, epic, story):
    with pytest.raises(Conflict):
        services.delete_epic(epic)
    assert Epic.objects.filter(pk=epic.pk).exists()
    services.update_story(story, epic=None)
    services.delete_epic(epic)
    assert not Epic.objects.filter(pk=epic.pk).exists()


def test_db_rejects_invalid_story_priority_and_task_has_no_epic_or_priority(project, make_story, make_task):
    story = make_story("h")
    with pytest.raises(IntegrityError), transaction.atomic():
        Story.objects.filter(pk=story.pk).update(priority="urgent")
    field_names = {f.name for f in Task._meta.get_fields()}
    assert not field_names & {"kind", "parent", "epic", "priority", "stakeholder"}


# ------------------------------------------------ épicas: vistas y permisos
def test_epic_views_roles(project, po, sm, dev, outsider, client_for):
    url = f"/projects/{project.pk}/epics/new/"
    data = {"title": "Pagos", "color": "#EAB308"}
    assert client_for(dev).post(url, data).status_code == 403
    assert client_for(outsider).post(url, data).status_code == 404
    assert client_for(sm).post(url, data).status_code == 302
    epic = Epic.objects.get(title="Pagos")
    edit = f"/epics/{epic.pk}/edit/"
    assert client_for(dev).post(edit, {"title": "X", "color": "#EAB308"}).status_code == 403
    assert client_for(sm).post(edit, {"title": "Cobros", "color": "#112233"}).status_code == 302
    epic.refresh_from_db()
    assert epic.title == "Cobros"
    assert client_for(sm).post(f"/epics/{epic.pk}/delete/").status_code == 403  # solo el PO borra
    assert client_for(po).post(f"/epics/{epic.pk}/delete/").status_code == 302
    assert not Epic.objects.exists()


def test_epic_view_invalid_color_is_422_and_delete_with_stories_is_409(project, po, sm, epic, story, client_for):
    r = client_for(sm).post(f"/projects/{project.pk}/epics/new/", {"title": "Mala", "color": "rojo"})
    assert r.status_code == 422
    assert not Epic.objects.filter(title="Mala").exists()
    assert client_for(po).post(f"/epics/{epic.pk}/delete/").status_code == 409


def test_epics_are_isolated_between_projects(project, po, epic, make_user, client_for):
    other_owner = make_user()
    other = project_services.create_project(other_owner, "Ajeno")
    c = client_for(other_owner)
    assert c.post(f"/epics/{epic.pk}/edit/", {"title": "X", "color": "#112233"}).status_code == 404
    assert c.post(f"/epics/{epic.pk}/delete/").status_code == 404
    r = c.post(f"/projects/{other.pk}/stories/new/", {"title": "Historia", "epic": epic.pk})
    assert r.status_code == 422  # la épica no es de su proyecto


def test_stories_page_groups_by_epic_and_filters(project, po, make_story, epic, story, client_for):
    make_story("Historia suelta")
    c = client_for(po)
    page = c.get(f"/projects/{project.pk}/stories/").content.decode()
    assert "Pagos" in page and "Historia de pago" in page
    assert "Sin épica" in page and "Historia suelta" in page
    assert page.index("Historia de pago") < page.index("Historia suelta")
    only = c.get(f"/projects/{project.pk}/stories/?epic={epic.pk}").content.decode()
    assert "Historia de pago" in only and "Historia suelta" not in only
    none = c.get(f"/projects/{project.pk}/stories/?epic=none").content.decode()
    assert "Historia suelta" in none and "Historia de pago" not in none


def test_story_form_accepts_epic_priority_and_points(project, sm, epic, client_for):
    r = client_for(sm).post(
        f"/projects/{project.pk}/stories/new/",
        {"title": "Nueva", "epic": epic.pk, "priority": "high", "estimate_points": 8},
    )
    assert r.status_code == 302
    story = Story.objects.get(title="Nueva")
    assert (story.epic_id, story.priority, story.estimate_points) == (epic.pk, "high", 8)
    assert r.url == f"/stories/{story.pk}/"


# ------------------------------------------------ criterios de aceptación
def test_criteria_services(project, story, make_task):
    c1 = services.add_criterion(story, "  Se envía recibo  ")
    c2 = services.add_criterion(story, "Se registra el pago")
    assert (c1.text, c1.position, c2.position) == ("Se envía recibo", 0, 1)
    assert list(story.criteria.all()) == [c1, c2]
    with pytest.raises(Unprocessable):
        services.add_criterion(story, "   ")
    with pytest.raises(Unprocessable):
        services.add_criterion(story, "x" * 501)
    assert not hasattr(make_task("tarea"), "criteria")  # los criterios solo existen en historias
    assert services.criteria_progress(story) == (0, 2)
    services.delete_criterion(c2)
    assert story.criteria.count() == 1


def test_toggle_criterion_requires_membership(project, story, dev, outsider):
    c = services.add_criterion(story, "Criterio")
    assert services.toggle_criterion(c, dev).is_done is True
    assert services.toggle_criterion(c, dev).is_done is False
    with pytest.raises(Forbidden):
        services.toggle_criterion(c, outsider)


def test_criteria_views_htmx_and_roles(project, story, sm, dev, outsider, client_for):
    add = f"/stories/{story.pk}/criteria/add/"
    assert client_for(dev).post(add, {"text": "No debería"}).status_code == 403
    assert client_for(outsider).post(add, {"text": "Fuera"}).status_code == 404
    r = client_for(sm).post(add, {"text": "Se envía recibo"}, **HX)
    assert r.status_code == 200 and "Se envía recibo" in r.content.decode() and "0 / 1 cumplidos" in r.content.decode()
    criterion = AcceptanceCriterion.objects.get()

    toggle = f"/criteria/{criterion.pk}/toggle/"
    r = client_for(dev).post(toggle, **HX)  # cualquier miembro marca
    assert r.status_code == 200 and "1 / 1 cumplidos" in r.content.decode()
    assert not r.content.decode().lstrip().startswith("<!doctype")  # es un fragmento, no la página
    criterion.refresh_from_db()
    assert criterion.is_done is True
    assert client_for(outsider).post(toggle, **HX).status_code == 404
    assert client_for(dev).post(f"/criteria/{criterion.pk}/delete/", **HX).status_code == 403
    assert client_for(sm).post(f"/criteria/{criterion.pk}/delete/", **HX).status_code == 200
    assert not AcceptanceCriterion.objects.exists()


def test_criteria_without_htmx_redirect_and_empty_text_shows_error(project, story, sm, client_for):
    c = client_for(sm)
    r = c.post(f"/stories/{story.pk}/criteria/add/", {"text": "Uno"})
    assert r.status_code == 302 and r.url.endswith("#criterios")
    r = c.post(f"/stories/{story.pk}/criteria/add/", {"text": ""}, **HX)
    assert r.status_code == 200 and "Escribe el criterio" in r.content.decode()


def test_story_detail_shows_criteria_progress_and_story_list_badge(project, po, story, client_for):
    c1 = services.add_criterion(story, "A")
    services.add_criterion(story, "B")
    services.toggle_criterion(c1, po)
    c = client_for(po)
    detail = c.get(f"/stories/{story.pk}/").content.decode()
    assert "Criterios de aceptación" in detail and "1 / 2 cumplidos" in detail
    assert "✓ 1/2" in c.get(f"/projects/{project.pk}/stories/").content.decode()


def test_criteria_are_removed_with_their_story(project, make_story):
    story = make_story("h")
    services.add_criterion(story, "x")
    story.delete()
    assert not AcceptanceCriterion.objects.exists()


# ------------------------------------------------ prioridad
def test_priority_default_validation_and_ordering(project, make_story):
    low = make_story("baja", priority="low")
    default = make_story("media")
    high = make_story("alta", priority="high")
    high2 = make_story("alta 2", priority="high")
    assert default.priority == "medium"
    with pytest.raises(Unprocessable):
        make_story("mala", priority="urgent")
    ordered = list(services.order_by_priority(Story.objects.filter(project=project)))
    assert ordered == [high, high2, default, low]


def test_backlog_filters_by_priority_and_epic(project, po, make_task, make_story, epic, client_for):
    story = make_story("Historia con épica", epic=epic, priority="high")
    make_task("Tarea alta hija", story=story)
    make_task("Tarea suelta")
    c = client_for(po)
    base = f"/projects/{project.pk}/backlog/"
    page = c.get(base).content.decode()
    assert page.index("Tarea alta hija") < page.index("Tarea suelta")  # alta primero
    high = c.get(base + "?priority=high").content.decode()
    assert "Tarea alta hija" in high and "Tarea suelta" not in high
    by_epic = c.get(base + f"?epic={epic.pk}").content.decode()
    assert "Tarea alta hija" in by_epic and "Tarea suelta" not in by_epic
    no_epic = c.get(base + "?epic=none").content.decode()
    assert "Tarea suelta" in no_epic and "Tarea alta hija" not in no_epic
    assert c.get(base + "?priority=basura&epic=abc").status_code == 200  # filtros inválidos se ignoran


# ------------------------------------------------ devolver al backlog
def test_unassign_sprint_rules(project, make_task, today, active_sprint):
    planned = sprint_services.create_sprint(project, "Futuro", start_date=today, end_date=today)
    task = make_task("t")
    services.assign_sprint(task, planned)
    task.refresh_from_db()
    assert task.sprint_id == planned.pk and task.column_id

    services.unassign_sprint(task)
    task.refresh_from_db()
    assert task.sprint_id is None and task.column_id is None
    with pytest.raises(Unprocessable):
        services.unassign_sprint(task)  # ya no tiene sprint

    sprint, (active_task, *_) = active_sprint(2)
    with pytest.raises(Conflict):
        services.unassign_sprint(active_task)
    active_task.refresh_from_db()
    assert active_task.sprint_id == sprint.pk


def test_unassign_sprint_view_roles_and_isolation(project, sm, dev, outsider, make_task, today, client_for):
    planned = sprint_services.create_sprint(project, "Futuro", start_date=today, end_date=today)
    task = make_task("t")
    services.assign_sprint(task, planned)
    url = f"/tasks/{task.pk}/unassign-sprint/"
    assert client_for(dev).post(url).status_code == 403
    assert client_for(outsider).post(url).status_code == 404
    assert client_for(sm).get(url).status_code == 405
    assert client_for(sm).post(url).status_code == 302
    task.refresh_from_db()
    assert task.sprint_id is None
    page = client_for(sm).get(f"/projects/{project.pk}/sprints/").content.decode()
    assert "Devolver al backlog" not in page  # ya no hay tareas en el sprint planificado


def test_sprints_page_offers_unassign_only_for_planned(project, sm, make_task, today, client_for):
    planned = sprint_services.create_sprint(project, "Futuro", start_date=today, end_date=today)
    task = make_task("t")
    services.assign_sprint(task, planned)
    page = client_for(sm).get(f"/projects/{project.pk}/sprints/").content.decode()
    assert "Devolver al backlog" in page and f"/tasks/{task.pk}/unassign-sprint/" in page


def test_unassign_view_conflict_on_active_sprint(project, sm, active_sprint, client_for):
    _, (task, *_) = active_sprint(1)
    assert client_for(sm).post(f"/tasks/{task.pk}/unassign-sprint/").status_code == 409


# ------------------------------------------------ métricas de sprint
def test_open_sprint_metrics(project, active_sprint, columns):
    sprint, (a, b, c) = active_sprint(3)
    Task.objects.filter(sprint=sprint).update(estimate_points=5)
    Task.objects.filter(pk=a.pk).update(column=columns["Hecho"])
    metrics, velocity = services.sprint_metrics(project)
    m = metrics[sprint.pk]
    assert (m["total_points"], m["done_points"], m["total_tasks"], m["done_tasks"], m["percent"]) == (15, 5, 3, 1, 33)
    assert velocity is None


def test_metrics_without_estimates_use_task_count(project, active_sprint, columns):
    sprint, (a, b) = active_sprint(2)
    Task.objects.filter(pk=a.pk).update(column=columns["Hecho"])
    m = services.sprint_metrics(project)[0][sprint.pk]
    assert (m["total_points"], m["total_tasks"], m["done_tasks"], m["percent"]) == (0, 2, 1, 50)


def test_closed_sprint_metrics_and_average_velocity(project, active_sprint, columns, sm, client_for):
    s1, (a, b, c) = active_sprint(3)
    Task.objects.filter(sprint=s1).update(estimate_points=5)
    Task.objects.filter(pk=a.pk).update(column=columns["Hecho"])
    services.close_sprint(s1)
    s2, (d, e) = active_sprint(2)
    Task.objects.filter(sprint=s2).update(estimate_points=5, column=columns["Hecho"])
    services.close_sprint(s2)

    metrics, velocity = services.sprint_metrics(project)
    assert metrics[s1.pk]["committed_points"] == 15 and metrics[s1.pk]["completed_points"] == 5
    assert metrics[s2.pk]["committed_points"] == 10 and metrics[s2.pk]["completed_points"] == 10
    assert velocity == 7.5
    page = client_for(sm).get(f"/projects/{project.pk}/sprints/").content.decode()
    assert "Velocidad promedio" in page and ("7,5" in page or "7.5" in page) and "puntos comprometidos" in page


def test_sprints_page_without_closed_sprints_has_no_velocity(project, sm, client_for):
    page = client_for(sm).get(f"/projects/{project.pk}/sprints/").content.decode()
    assert "aún no hay sprints cerrados" in page


# ------------------------------------------------ tablero
def test_board_card_shows_story_epic_priority_and_criteria(project, po, epic, make_story, active_sprint, client_for):
    story = make_story("Historia de alta", epic=epic, priority="high")
    services.add_criterion(story, "Uno")
    services.add_criterion(story, "Dos")
    services.toggle_criterion(story.criteria.first(), po)
    active_sprint(1, story=story)
    page = client_for(po).get(f"/projects/{project.pk}/board/").content.decode()
    assert "#AA00CC" in page.upper()  # color de la épica
    assert "Historia de alta" in page and f"/stories/{story.pk}/" in page
    assert "Alta" in page and "✓ 1/2" in page


def test_board_card_without_story_is_clean(project, po, active_sprint, client_for):
    active_sprint(1)
    page = client_for(po).get(f"/projects/{project.pk}/board/").content.decode()
    assert "epic-dot" not in page and "Alta" not in page


def test_get_board_uses_constant_queries_for_context(project, make_story, epic, active_sprint, django_assert_max_num_queries):
    story = make_story("h", epic=epic)
    active_sprint(4, story=story)
    with django_assert_max_num_queries(12):
        services.get_board(project)


# ------------------------------------------------ datos de demostración
@pytest.mark.django_db
def test_seed_demo_creates_epics_criteria_and_priorities_and_is_repeatable():
    call_command("seed_demo", verbosity=0)
    assert Epic.objects.exists()
    assert AcceptanceCriterion.objects.exists()
    assert Story.objects.filter(priority="high").exists()
    assert Story.objects.filter(epic__isnull=False).exists()
    before = (Epic.objects.count(), AcceptanceCriterion.objects.count())
    call_command("seed_demo", verbosity=0)
    assert (Epic.objects.count(), AcceptanceCriterion.objects.count()) == before


# ------------------------------------------------ historias y tareas separadas
def test_story_detail_lists_tasks_and_creates_them(project, sm, dev, story, client_for):
    c = client_for(sm)
    r = c.post(f"/stories/{story.pk}/tasks/new/", {"title": "Integrar pasarela", "estimate_points": 3, "assignee": dev.pk})
    assert r.status_code == 302
    task = Task.objects.get()
    assert (task.story_id, task.estimate_points, task.assignee_id) == (story.pk, 3, dev.pk)
    page = c.get(f"/stories/{story.pk}/").content.decode()
    assert "Integrar pasarela" in page and "Asignar toda la historia" not in page  # sin sprint abierto


def test_story_detail_requires_membership_and_isolation(project, story, outsider, client_for):
    assert client_for(outsider).get(f"/stories/{story.pk}/").status_code == 404


def test_story_edit_and_delete_roles(project, po, sm, dev, story, make_task, client_for):
    url = f"/stories/{story.pk}/edit/"
    assert client_for(dev).get(url).status_code == 403
    assert client_for(sm).get(url).status_code == 200
    assert client_for(sm).post(url, {"title": "Nuevo título", "priority": "low"}).status_code == 302
    story.refresh_from_db()
    assert (story.title, story.priority) == ("Nuevo título", "low")
    make_task("hija", story=story)
    assert client_for(sm).post(f"/stories/{story.pk}/delete/").status_code == 403
    assert client_for(po).post(f"/stories/{story.pk}/delete/").status_code == 409  # tiene tareas
    Task.objects.all().delete()
    assert client_for(po).post(f"/stories/{story.pk}/delete/").status_code == 302
    assert not Story.objects.exists()


def test_story_assign_sprint_button_visible_with_open_sprint(project, sm, story, make_task, today, client_for):
    make_task("hija", story=story)
    sprint_services.create_sprint(project, "Futuro", start_date=today, end_date=today)
    page = client_for(sm).get(f"/stories/{story.pk}/").content.decode()
    assert "Asignar toda la historia" in page


def test_comment_xor_story_or_task(project, po, story, make_task):
    task = make_task("t")
    with pytest.raises(IntegrityError), transaction.atomic():
        Comment.objects.create(author=po, body="ninguno")
    with pytest.raises(IntegrityError), transaction.atomic():
        Comment.objects.create(author=po, body="ambos", story=story, task=task)
    on_story = services.add_comment(story, po, "a la historia")
    on_task = services.add_comment(task, po, "a la tarea")
    assert on_story.target == story and on_task.target == task
    assert on_story.project == project and on_task.project == project


def test_comment_delete_redirects_to_story_or_task(project, po, story, make_task, client_for):
    task = make_task("t")
    c = client_for(po)
    cs = services.add_comment(story, po, "x")
    ct = services.add_comment(task, po, "y")
    assert c.post(f"/comments/{cs.pk}/delete/").url.startswith(f"/stories/{story.pk}/")
    assert c.post(f"/comments/{ct.pk}/delete/").url.startswith(f"/tasks/{task.pk}/")


def test_task_story_is_protected_and_task_detail_links_story(project, po, story, make_task, client_for):
    task = make_task("t", story=story)
    with pytest.raises(Conflict):
        services.delete_story(story)
    page = client_for(po).get(f"/tasks/{task.pk}/").content.decode()
    assert f"/stories/{story.pk}/" in page


def test_story_unassigned_tasks_assigned_together_via_view(project, sm, story, make_task, today, client_for):
    a, b = make_task("a", story=story), make_task("b", story=story)
    sprint = sprint_services.create_sprint(project, "Futuro", start_date=today, end_date=today)
    r = client_for(sm).post(f"/stories/{story.pk}/assign-sprint/", {"sprint_id": sprint.pk})
    assert r.status_code == 302 and r.url == f"/stories/{story.pk}/"
    a.refresh_from_db()
    b.refresh_from_db()
    assert a.sprint_id == b.sprint_id == sprint.pk
