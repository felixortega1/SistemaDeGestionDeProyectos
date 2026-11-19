import pytest
from django.db import IntegrityError, transaction

from apps.backlog import services
from apps.backlog.models import Task
from apps.core.exceptions import Conflict, Unprocessable
from apps.projects import services as project_services
from apps.sprints import services as sprint_services


def test_dependency_rules(project, make_task, po):
    a, b, c = make_task("a"), make_task("b"), make_task("c")
    story = make_task("hist", kind="story")
    services.add_dependency(b, a)
    services.add_dependency(c, b)
    with pytest.raises(Unprocessable):
        services.add_dependency(a, c)  # ciclo
    with pytest.raises(Unprocessable):
        services.add_dependency(a, a)
    with pytest.raises(Unprocessable):
        services.add_dependency(b, a)  # duplicado
    with pytest.raises(Unprocessable):
        services.add_dependency(a, story)
    other = project_services.create_project(po, "B")
    foreign = services.create_task(other, title="x")
    with pytest.raises(Unprocessable):
        services.add_dependency(a, foreign)


def test_reference_validation(project, po, make_task):
    task = make_task("t")
    with pytest.raises(Unprocessable):
        make_task("y", parent=task)  # el padre debe ser historia
    with pytest.raises(Unprocessable):
        make_task("s", kind="story", due_date="2030-01-01")


def test_assignee_must_be_member(project, make_user, make_task):
    with pytest.raises(Unprocessable):
        make_task("x", assignee=make_user())


def test_sprint_and_column_go_together(project, make_task):
    t = make_task()
    t.column = project.columns.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        t.save()


def test_assign_sprint_rules(project, make_task, columns, today):
    t, story = make_task(), make_task("s", kind="story")
    sprint = sprint_services.create_sprint(project, "S")
    services.assign_sprint(t, sprint)
    t.refresh_from_db()
    assert t.column_id == columns["Por hacer"].pk and t.sprint_id == sprint.pk
    with pytest.raises(Unprocessable):
        services.assign_sprint(t, sprint)  # ya tiene sprint
    with pytest.raises(Unprocessable):
        services.assign_sprint(story, sprint)


def test_assign_to_closed_sprint_rejected(project, make_task, active_sprint):
    sprint, tasks = active_sprint(1)
    services.close_sprint(sprint)
    with pytest.raises(Unprocessable):
        services.assign_sprint(make_task("nueva"), sprint)


def test_assign_active_sprint_with_wip_zero(project, make_task, active_sprint, columns):
    sprint, _ = active_sprint(1)
    first = columns["Por hacer"]
    first.wip_limit = 0
    first.save()
    with pytest.raises(Conflict):
        services.assign_sprint(make_task("otra"), sprint)


def test_delete_protected(project, make_task, active_sprint):
    parent = make_task("p", kind="story")
    child = make_task("c", parent=parent)
    with pytest.raises(Conflict):
        services.delete_task(parent)
    services.delete_task(child)
    services.delete_task(parent)
    sprint, (t, *_) = active_sprint(1)
    with pytest.raises(Conflict):
        services.delete_task(t)
    dep_a, dep_b = make_task("da"), make_task("db")
    services.add_dependency(dep_b, dep_a)
    with pytest.raises(Conflict):
        services.delete_task(dep_a)


def test_stale_edit_does_not_overwrite_placement(project, make_task, active_sprint, columns):
    sprint, (t, *_) = active_sprint(1)
    stale = Task.objects.get(pk=t.pk)
    services.move_task(t, columns["En desarrollo"], project.created_by)
    services.update_task(stale, title="nuevo título")
    fresh = Task.objects.get(pk=t.pk)
    assert fresh.title == "nuevo título"
    assert fresh.column_id == columns["En desarrollo"].pk and fresh.sprint_id == sprint.pk
