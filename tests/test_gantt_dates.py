import datetime
from types import SimpleNamespace as NS

from apps.backlog import services
from apps.gantt.services import build_gantt, effective_dates
from apps.sprints import services as sprint_services

D = datetime.date


def task(start=None, due=None):
    return NS(start_date=start, due_date=due)


def sprint(start=None, end=None):
    return NS(start_date=start, end_date=end)


def test_effective_dates_inherit_and_override():
    s = sprint(D(2026, 1, 1), D(2026, 1, 10))
    e = effective_dates(task(), s)
    assert (e["start"], e["end"], e["start_source"], e["end_source"]) == (D(2026, 1, 1), D(2026, 1, 10), "sprint", "sprint")
    e = effective_dates(task(D(2026, 1, 3), D(2026, 1, 4)), s)
    assert (e["start"], e["end"], e["start_source"]) == (D(2026, 1, 3), D(2026, 1, 4), "task")
    e = effective_dates(task(D(2026, 1, 3)), s)  # inicio propio, fin del sprint
    assert e["start_source"] == "task" and e["end_source"] == "sprint"


def test_undated_reasons():
    assert effective_dates(task(), None)["undated"] == "sin fechas"
    assert effective_dates(task(D(2026, 1, 1)), None)["undated"] == "una sola fecha"
    assert effective_dates(task(), sprint(D(2026, 1, 1), None))["undated"] == "una sola fecha"
    assert effective_dates(task(D(2026, 2, 1), D(2026, 1, 1)), None)["undated"] == "fin anterior al inicio"


def test_late_marks(project, active_sprint, today, columns):
    s, (a, b) = active_sprint(2)
    from apps.backlog.models import Task

    Task.objects.filter(pk=b.pk).update(column=columns["Hecho"])
    data = build_gantt(project, today)
    late = {t["title"]: t["is_late"] for t in data["tasks"]}
    assert late == {"T0": True, "T1": False}
    assert build_gantt(project, today - datetime.timedelta(days=30))["tasks"][0]["is_late"] is False


def test_unsprinted_task_never_late(project, make_task, today):
    make_task("x", start_date=today - datetime.timedelta(days=9), due_date=today - datetime.timedelta(days=8))
    assert build_gantt(project, today)["tasks"][0]["is_late"] is False


def test_conflict_and_depends_on(project, make_task, today):
    a = make_task("a", start_date=D(2026, 3, 1), due_date=D(2026, 3, 5))
    b = make_task("b", start_date=D(2026, 3, 5), due_date=D(2026, 3, 8))  # empieza el día que termina a
    c = make_task("c", start_date=D(2026, 3, 6), due_date=D(2026, 3, 9))
    nodate = make_task("sin")
    services.add_dependency(b, a)
    services.add_dependency(c, a)
    services.add_dependency(nodate, a)
    data = build_gantt(project, today)
    by = {t["title"]: t for t in data["tasks"]}
    assert by["b"]["conflict"] is True and by["c"]["conflict"] is False
    assert by["b"]["depends_on"] == [a.pk]
    assert [u["title"] for u in data["undated"]] == ["sin"]
    assert "sin" not in by


def test_same_sprint_inheritance_is_not_conflict(project, make_task, today):
    sp = sprint_services.create_sprint(project, "S", start_date=D(2026, 4, 1), end_date=D(2026, 4, 10))
    a, b = make_task("a"), make_task("b")
    services.assign_sprint(a, sp)
    services.assign_sprint(b, sp)
    services.add_dependency(b, a)
    assert [t["conflict"] for t in build_gantt(project, today)["tasks"]] == [False, False]


def test_gantt_page_embeds_json(project, po, active_sprint, client_for):
    active_sprint(1)
    r = client_for(po).get(f"/projects/{project.pk}/gantt/")
    assert r.status_code == 200 and b'id="gantt-data"' in r.content and b'"is_late": true' in r.content
