from apps.backlog.models import Task

HX = {"HTTP_HX_REQUEST": "true"}


def test_htmx_move_fragments(project, po, active_sprint, columns, client_for):
    sprint, tasks = active_sprint(4)
    c = client_for(po)
    dev = columns["En desarrollo"]
    for t in tasks[:3]:
        r = c.post(f"/tasks/{t.pk}/move/", {"column_id": dev.pk}, **HX)
        assert r.status_code == 200 and b'id="board"' in r.content
    assert b"3 / 3" in r.content

    r = c.post(f"/tasks/{tasks[3].pk}/move/", {"column_id": dev.pk}, **HX)
    assert r.status_code == 409 and "límite WIP".encode() in r.content and b'id="board"' in r.content

    r = c.post(f"/tasks/{tasks[3].pk}/move/", {"column_id": columns["Hecho"].pk}, **HX)
    assert r.status_code == 422 and "En desarrollo".encode() in r.content
    assert Task.objects.get(pk=tasks[3].pk).column_id == columns["Por hacer"].pk


def test_non_htmx_move_redirects_with_message(project, po, active_sprint, columns, client_for):
    sprint, (t, *_) = active_sprint(1)
    c = client_for(po)
    r = c.post(f"/tasks/{t.pk}/move/", {"column_id": columns["Hecho"].pk})
    assert r.status_code == 302 and r.url == f"/projects/{project.pk}/board/"
    r = c.get(r.url)
    assert "No se puede mover".encode() in r.content


def test_select_move_form_is_rendered_and_works(project, po, active_sprint, columns, client_for):
    sprint, (t, *_) = active_sprint(1)
    c = client_for(po)
    page = c.get(f"/projects/{project.pk}/board/")
    assert b"Mover a" in page.content and b"0 / 3" in page.content
    r = c.post(f"/tasks/{t.pk}/move/", {"column_id": columns["En desarrollo"].pk})
    assert r.status_code == 302
    assert b"1 / 3" in c.get(r.url).content


def test_no_active_sprint_message(project, po, client_for):
    assert "No hay un sprint activo".encode() in client_for(po).get(f"/projects/{project.pk}/board/").content


def test_developer_can_move_only_own_or_unassigned(project, dev, add_member, active_sprint, columns, client_for):
    sprint, (mine, theirs, free) = active_sprint(3)
    other = add_member(project, "developer")
    mine.assignee, theirs.assignee = dev, other
    mine.save(), theirs.save()
    c = client_for(dev)
    todo = columns["En desarrollo"]
    assert c.post(f"/tasks/{mine.pk}/move/", {"column_id": todo.pk}).status_code == 302
    assert c.post(f"/tasks/{free.pk}/move/", {"column_id": todo.pk}).status_code == 302
    assert c.post(f"/tasks/{theirs.pk}/move/", {"column_id": todo.pk}).status_code == 403


def test_comment_from_kanban_card_htmx(project, po, dev, active_sprint, client_for):
    from apps.backlog.models import Comment

    sprint, (t, *_) = active_sprint(1)
    c = client_for(dev)
    r = c.post(f"/tasks/{t.pk}/board-comment/", {"body": "Voy a empezar mañana"}, **HX)
    assert r.status_code == 200 and b'id="board"' in r.content and b"Voy a empezar" in r.content
    assert b"Comentarios (1)" in r.content and b"Comentario guardado" in r.content
    assert Comment.objects.get().author == dev
    r = c.post(f"/tasks/{t.pk}/board-comment/", {"body": "  "}, **HX)
    assert r.status_code == 422 and Comment.objects.count() == 1


def test_comment_from_kanban_without_htmx_redirects(project, po, active_sprint, client_for):
    sprint, (t, *_) = active_sprint(1)
    r = client_for(po).post(f"/tasks/{t.pk}/board-comment/", {"body": "hola"})
    assert r.status_code == 302 and r.url == f"/projects/{project.pk}/board/"


def test_outsider_cannot_comment_from_kanban(project, make_user, active_sprint, client_for):
    sprint, (t, *_) = active_sprint(1)
    assert client_for(make_user()).post(f"/tasks/{t.pk}/board-comment/", {"body": "hola"}, **HX).status_code == 404


def test_diagrams_menu_has_kanban_and_gantt(project, po, client_for):
    c = client_for(po)
    board = c.get(f"/projects/{project.pk}/board/").content
    gantt = c.get(f"/projects/{project.pk}/gantt/").content
    for page in (board, gantt):
        assert b"Diagramas" in page and b"Kanban" in page and b"Gantt" in page
        assert b">Tablero<" not in page
    assert project.name.encode() in gantt  # el título del proyecto aparece en el Gantt


def test_non_po_sees_why_they_cannot_create_stories(project, po, dev, client_for):
    page = client_for(dev).get(f"/projects/{project.pk}/stories/").content
    assert b"Las historias las crean" in page and b"Nueva historia" not in page
    assert b"Nueva historia" in client_for(po).get(f"/projects/{project.pk}/stories/").content
