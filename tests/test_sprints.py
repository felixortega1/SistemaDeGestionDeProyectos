import datetime

import pytest
from django.db import IntegrityError, transaction

from apps.backlog import services as backlog
from apps.backlog.models import SprintTask, Task
from apps.core.exceptions import Conflict, Unprocessable
from apps.sprints import services
from apps.sprints.models import Sprint


def test_second_active_sprint_is_409(project, active_sprint, today):
    active_sprint(1)
    s2 = services.create_sprint(project, "S2", start_date=today, end_date=today)
    with pytest.raises(Conflict):
        services.start_sprint(s2)


def test_unique_index_rejects_second_active(project, active_sprint, today):
    active_sprint(1)
    s2 = services.create_sprint(project, "S2", start_date=today, end_date=today)
    with pytest.raises(IntegrityError), transaction.atomic():
        Sprint.objects.filter(pk=s2.pk).update(status="active")


def test_start_requires_planned_and_dates(project, active_sprint):
    sprint, _ = active_sprint(1)
    with pytest.raises(Conflict):
        services.start_sprint(sprint)
    undated = services.create_sprint(project, "sin fechas")
    with pytest.raises(Unprocessable):
        services.start_sprint(undated)


def test_end_before_start_rejected(project, today):
    with pytest.raises(Unprocessable):
        services.create_sprint(project, "x", start_date=today, end_date=today - datetime.timedelta(days=1))


def test_close_sprint_keeps_done_and_returns_rest(project, active_sprint, columns):
    sprint, (done, doing, todo) = active_sprint(3)
    Task.objects.filter(pk=done.pk).update(column=columns["Hecho"])
    Task.objects.filter(pk=doing.pk).update(column=columns["En desarrollo"])
    Task.objects.filter(sprint=sprint).update(estimate_points=5)
    backlog.close_sprint(sprint, "review", "retro")

    done.refresh_from_db(), doing.refresh_from_db(), todo.refresh_from_db()
    assert done.sprint_id == sprint.pk and done.column_id == columns["Hecho"].pk
    assert doing.sprint_id is None and doing.column_id is None
    assert todo.sprint_id is None and todo.column_id is None
    rows = {r.task_id: r for r in SprintTask.objects.filter(sprint=sprint)}
    assert len(rows) == 3
    assert rows[done.pk].is_done and rows[done.pk].column_name == "Hecho" and rows[done.pk].estimate_points == 5
    assert not rows[doing.pk].is_done and rows[doing.pk].column_name == "En desarrollo"
    sprint.refresh_from_db()
    assert sprint.status == "closed" and sprint.review_notes == "review" and sprint.retro_notes == "retro"


def test_second_close_rejected_without_duplicates(project, active_sprint):
    sprint, _ = active_sprint(2)
    backlog.close_sprint(sprint)
    with pytest.raises(Conflict):
        backlog.close_sprint(sprint)
    assert SprintTask.objects.filter(sprint=sprint).count() == 2
