import pytest

from apps.backlog import services

P = "/projects/{}"


def test_matrix_projects_tasks_sprints(project, po, sm, dev, make_task, client_for):
    t = make_task("x")
    new_task = {"title": "nueva"}
    url = f"/projects/{project.pk}/tasks/new/"
    assert client_for(po).post(url, new_task).status_code == 302
    assert client_for(sm).post(url, new_task).status_code == 403
    assert client_for(dev).post(url, new_task).status_code == 403

    sprint_url = f"/projects/{project.pk}/sprints/new/"
    assert client_for(po).post(sprint_url, {"name": "S"}).status_code == 302
    assert client_for(sm).post(sprint_url, {"name": "S2"}).status_code == 302
    assert client_for(dev).post(sprint_url, {"name": "S3"}).status_code == 403

    assert client_for(dev).post(f"/tasks/{t.pk}/delete/").status_code == 403
    assert client_for(sm).post(f"/tasks/{t.pk}/delete/").status_code == 403
    assert client_for(po).post(f"/tasks/{t.pk}/delete/").status_code == 302

    for user in (po, sm, dev):
        assert client_for(user).get(f"/projects/{project.pk}/backlog/").status_code == 200


def test_edit_task_permissions(project, po, sm, dev, make_task, client_for):
    mine = make_task("mia", assignee=dev)
    other = make_task("ajena")
    assert client_for(dev).get(f"/tasks/{mine.pk}/edit/").status_code == 200
    assert client_for(dev).get(f"/tasks/{other.pk}/edit/").status_code == 403
    # el developer no puede cambiar el responsable: el campo no existe en su formulario
    r = client_for(dev).post(f"/tasks/{mine.pk}/edit/", {"title": "otra", "assignee": po.pk})
    assert r.status_code == 302
    mine.refresh_from_db()
    assert mine.title == "otra" and mine.assignee_id == dev.pk
    # el Scrum Master solo asigna
    r = client_for(sm).post(f"/tasks/{other.pk}/edit/", {"assignee": dev.pk, "title": "hack"})
    assert r.status_code == 302
    other.refresh_from_db()
    assert other.assignee_id == dev.pk and other.title == "ajena"


def test_members_management_is_po_only(project, po, sm, dev, make_user, client_for):
    u = make_user("nuevo@example.com")
    url = f"/projects/{project.pk}/members/add/"
    assert client_for(sm).post(url, {"email": u.email, "role": "developer"}).status_code == 403
    assert client_for(po).post(url, {"email": u.email, "role": "developer"}).status_code == 302


def test_columns_editing_roles(project, po, sm, dev, columns, client_for):
    url = f"/columns/{columns['Por hacer'].pk}/edit/"
    data = {"name": "Backlog", "wip_limit": "", "policy_text": ""}
    assert client_for(dev).post(url, data).status_code == 403
    assert client_for(sm).post(url, data).status_code == 302
    assert client_for(po).post(url, {**data, "name": "Por hacer"}).status_code == 302


def test_assign_and_close_are_sm_up(project, po, sm, dev, make_task, client_for):
    from apps.sprints import services as sprint_services

    t = make_task()
    s = sprint_services.create_sprint(project, "S")
    url = f"/tasks/{t.pk}/assign-sprint/"
    assert client_for(dev).post(url, {"sprint_id": s.pk}).status_code == 403
    assert client_for(sm).post(url, {"sprint_id": s.pk}).status_code == 302
    assert services is not None


@pytest.mark.parametrize("page", ["backlog", "sprints", "board", "gantt", "budget"])
def test_pages_render_for_members(project, dev, client_for, page):
    assert client_for(dev).get(f"/projects/{project.pk}/{page}/").status_code == 200


def test_columns_page_forbidden_for_dev(project, dev, client_for):
    assert client_for(dev).get(f"/projects/{project.pk}/columns/").status_code == 403
