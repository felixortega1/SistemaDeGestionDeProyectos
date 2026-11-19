import pytest

from apps.backlog import services
from apps.board import services as board
from apps.board.models import BoardColumn, ColumnTransition
from apps.core.exceptions import Unprocessable
from apps.projects import services as project_services


def test_contiguous_allowed_and_todo_to_done_rejected(project, po, active_sprint, columns):
    sprint, (t, *_) = active_sprint(1)
    with pytest.raises(Unprocessable) as exc:
        services.move_task(t, columns["Hecho"], po)
    assert "En desarrollo" in exc.value.message
    services.move_task(t, columns["En desarrollo"], po)
    services.move_task(t, columns["En revisión"], po)
    services.move_task(t, columns["Hecho"], po)
    services.move_task(t, columns["En revisión"], po)  # y de vuelta


def test_edited_transitions_via_views(project, sm, dev, po, columns, client_for):
    a, d = columns["Por hacer"], columns["Hecho"]
    pairs = [("transition", f"{a.pk}_{d.pk}")]
    url = f"/projects/{project.pk}/columns/transitions/"
    assert client_for(dev).post(url, dict(pairs)).status_code == 403
    assert client_for(sm).post(url, dict(pairs)).status_code == 302
    stored = ColumnTransition.objects.filter(from_column__project=project).values_list("from_column_id", "to_column_id")
    assert list(stored) == [(a.pk, d.pk)]
    assert client_for(po).post(url, {"transition": f"{d.pk}_{a.pk}"}).status_code == 302


def test_transition_with_foreign_column_is_422(project, po, columns):
    other = project_services.create_project(po, "B")
    foreign = other.columns.first()
    with pytest.raises(Unprocessable):
        board.set_transitions(project, [(columns["Por hacer"].pk, foreign.pk)])


def test_create_column_inserts_before_done(project, columns):
    new = board.create_column(project, "QA", 2, "pruebas")
    ordered = list(BoardColumn.objects.filter(project=project))
    assert [c.name for c in ordered] == ["Por hacer", "En desarrollo", "En revisión", "QA", "Hecho"]
    assert ordered[-1].is_done
    pairs = set(ColumnTransition.objects.filter(from_column__project=project).values_list("from_column_id", "to_column_id"))
    rev, done = columns["En revisión"], columns["Hecho"]
    assert {(rev.pk, new.pk), (new.pk, rev.pk), (new.pk, done.pk), (done.pk, new.pk)} <= pairs
    assert (rev.pk, done.pk) in pairs  # no se borran las existentes
