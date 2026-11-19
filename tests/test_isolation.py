from apps.backlog import services
from apps.projects import services as project_services
from apps.sprints import services as sprint_services


def test_other_project_user_gets_404(project, make_task, make_user, client_for):
    task = make_task("x")
    sprint = sprint_services.create_sprint(project, "S")
    outsider = make_user("out@example.com")
    project_services.create_project(outsider, "B")
    c = client_for(outsider)
    assert c.get(f"/tasks/{task.pk}/edit/").status_code == 404
    assert c.post(f"/tasks/{task.pk}/delete/").status_code == 404
    assert c.post(f"/tasks/{task.pk}/move/", {"column_id": 1}).status_code == 404
    assert c.post(f"/sprints/{sprint.pk}/start/").status_code == 404
    assert c.post(f"/sprints/{sprint.pk}/close/").status_code == 404
    for page in ("backlog", "sprints", "board", "gantt", "budget", "members", "columns"):
        assert c.get(f"/projects/{project.pk}/{page}/").status_code == 404


def test_department_isolation(project, po, make_user, client_for):
    from apps.budget.models import Department

    d = Department.objects.create(project=project, name="X", budget_amount=1, currency="USD", updated_by=po)
    outsider = make_user("out2@example.com")
    project_services.create_project(outsider, "B")
    c = client_for(outsider)
    assert c.post(f"/departments/{d.pk}/edit/", {"name": "Y", "budget_amount": "2", "currency": "USD"}).status_code == 404
    assert c.post(f"/departments/{d.pk}/delete/").status_code == 404


def test_cannot_assign_foreign_sprint(project, po, make_task, client_for):
    other = project_services.create_project(po, "B")
    foreign = sprint_services.create_sprint(other, "S")
    task = make_task()
    r = client_for(po).post(f"/tasks/{task.pk}/assign-sprint/", {"sprint_id": foreign.pk})
    assert r.status_code == 404
    assert services is not None
