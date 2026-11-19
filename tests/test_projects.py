import pytest

from apps.board.models import ColumnTransition
from apps.core.exceptions import Conflict, Unprocessable
from apps.projects import services
from apps.projects.models import ProjectMember


def test_create_project_defaults(project, po):
    cols = list(project.columns.all())
    assert [c.name for c in cols] == ["Por hacer", "En desarrollo", "En revisión", "Hecho"]
    assert cols[1].wip_limit == 3 and cols[3].is_done
    pairs = set(ColumnTransition.objects.filter(from_column__project=project).values_list("from_column_id", "to_column_id"))
    for a, b in zip(cols, cols[1:]):
        assert (a.pk, b.pk) in pairs and (b.pk, a.pk) in pairs
    assert (cols[0].pk, cols[3].pk) not in pairs
    assert project.members.get().role == ProjectMember.PRODUCT_OWNER


def test_transfer_po_is_atomic_and_sets_outgoing_role(project, po, dev):
    services.transfer_product_owner(project, dev.pk, ProjectMember.SCRUM_MASTER)
    roles = {m.user_id: m.role for m in project.members.all()}
    assert roles[dev.pk] == "product_owner" and roles[po.pk] == "scrum_master"
    assert sum(1 for r in roles.values() if r == "product_owner") == 1


def test_role_change_rejects_product_owner(project, dev):
    with pytest.raises(Unprocessable):
        services.change_role(project, dev.pk, "product_owner")


def test_cannot_remove_po(project, po):
    with pytest.raises(Conflict):
        services.remove_member(project, po.pk)


def test_remove_member_with_unfinished_tasks_is_409(project, dev, make_task, active_sprint, columns):
    from apps.backlog import services as backlog

    sprint, (t, *_) = active_sprint(1)
    t.assignee = dev
    t.save()
    with pytest.raises(Conflict):
        services.remove_member(project, dev.pk)
    done = columns["Hecho"]
    from apps.backlog.models import Task

    Task.objects.filter(pk=t.pk).update(column=done)
    services.remove_member(project, dev.pk)
    assert backlog is not None


def test_add_member_unknown_email(project):
    with pytest.raises(Unprocessable):
        services.add_member(project, "nadie@example.com", "developer")


def test_add_member_by_view(project, po, make_user, client_for):
    other = make_user("other@example.com")
    c = client_for(po)
    r = c.post(f"/projects/{project.pk}/members/add/", {"email": other.email, "role": "developer"})
    assert r.status_code == 302
    assert project.members.filter(user=other).exists()
    r = c.get(f"/projects/{project.pk}/")
    assert r.status_code == 302 and r.url == f"/projects/{project.pk}/stories/"
