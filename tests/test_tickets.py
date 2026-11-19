import datetime

import pytest
from django.utils import timezone

from apps.core.exceptions import Forbidden, Unprocessable
from apps.projects import services as projects
from apps.tickets import services
from apps.tickets.models import Ticket

HX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def pm(project, add_member):
    return add_member(project, "project_manager")


def test_user_creates_own_ticket_in_their_company(project, dev):
    t = services.create_ticket(dev, company=project.company, title="Revisar correo")
    assert t.assignee == dev and t.created_by == dev and t.date == timezone.localdate()


def test_cannot_create_ticket_in_company_without_membership(project, dev, make_user):
    foreign = projects.create_project(make_user(), "Ajeno", company_name="Otra empresa").company
    with pytest.raises(Unprocessable):
        services.create_ticket(dev, company=foreign, title="No")


@pytest.mark.parametrize("who", ["po", "pm", "sm"])
def test_po_pm_sm_can_assign_tickets_to_others(project, po, pm, sm, dev, who):
    user = {"po": po, "pm": pm, "sm": sm}[who]
    t = services.create_ticket(user, company=project.company, title="Para ti", assignee=dev)
    assert t.assignee == dev and t.created_by == user


def test_developer_cannot_assign_to_others(project, dev, po):
    with pytest.raises(Forbidden):
        services.create_ticket(dev, company=project.company, title="No", assignee=po)
    assert Ticket.objects.count() == 0


def test_assignee_must_belong_to_the_company(project, po, make_user):
    outsider = make_user()
    with pytest.raises(Unprocessable):
        services.create_ticket(po, company=project.company, title="X", assignee=outsider)


def test_manager_role_counts_per_company(project, po, make_user):
    """Ser responsable en una empresa no da permiso de asignar en otra."""
    from apps.projects.models import ProjectMember

    owner_beta = make_user()
    beta = projects.create_project(owner_beta, "Otro", company_name="Beta")
    ProjectMember.objects.create(project=beta, user=po, role="developer")  # po solo es desarrollo en Beta
    with pytest.raises(Forbidden):
        services.create_ticket(po, company=beta.company, title="X", assignee=owner_beta)
    assert services.create_ticket(po, company=project.company, title="Y", assignee=po)


def test_panel_shows_only_my_tickets_for_my_companies(project, po, dev, make_user, client_for):
    services.create_ticket(dev, company=project.company, title="Mi ticket")
    services.create_ticket(po, company=project.company, title="Ticket de otra persona")
    stranger = make_user()
    other = projects.create_project(stranger, "Ajeno", company_name="Otra empresa")
    services.create_ticket(stranger, company=other.company, title="De una empresa ajena")
    page = client_for(dev).get("/tickets/panel/", **HX).content
    assert b"Mi ticket" in page
    assert b"Ticket de otra persona" not in page and b"De una empresa ajena" not in page


def test_pending_tickets_carry_over_but_done_ones_do_not(project, dev):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    old_open = services.create_ticket(dev, company=project.company, title="Viejo pendiente", date=yesterday)
    old_done = services.create_ticket(dev, company=project.company, title="Viejo hecho", date=yesterday)
    services.toggle_ticket(old_done, dev)
    titles = [t.title for t in services.tickets_for(dev)]
    assert "Viejo pendiente" in titles and "Viejo hecho" not in titles
    assert services.open_count(dev) == 1 and old_open.status == "open"


def test_toggle_and_permissions(project, dev, po, add_member):
    t = services.create_ticket(po, company=project.company, title="Tuyo", assignee=dev)
    services.toggle_ticket(t, dev)
    assert Ticket.objects.get().status == "done"
    services.toggle_ticket(t, po)  # quien lo creó también puede reabrirlo
    assert Ticket.objects.get().status == "open"
    other = add_member(project, "developer")
    with pytest.raises(Forbidden):
        services.toggle_ticket(t, other)


def test_delete_permissions(project, dev, po, add_member):
    t = services.create_ticket(po, company=project.company, title="X", assignee=dev)
    with pytest.raises(Forbidden):
        services.delete_ticket(t, dev)  # la persona asignada no lo creó ni es responsable
    services.delete_ticket(t, po)
    assert Ticket.objects.count() == 0


def test_views_create_toggle_delete_htmx(project, po, dev, client_for):
    c = client_for(po)
    data = {"title": "Preparar la reunión", "company": project.company_id, "assignee": dev.pk}
    r = c.post("/tickets/new/", data, **HX)
    assert r.status_code == 200 and b"Ticket creado" in r.content
    t = Ticket.objects.get()
    assert t.assignee == dev
    r = client_for(dev).post(f"/tickets/{t.pk}/toggle/", {}, **HX)
    assert r.status_code == 200 and Ticket.objects.get().status == "done"
    assert client_for(dev).post(f"/tickets/{t.pk}/delete/", {}, **HX).status_code == 422
    assert c.post(f"/tickets/{t.pk}/delete/", {}, **HX).status_code == 200
    assert Ticket.objects.count() == 0


def test_view_rejects_developer_assigning_others_and_outsiders(project, po, dev, make_user, client_for):
    r = client_for(dev).post("/tickets/new/", {"title": "X", "company": project.company_id, "assignee": po.pk}, **HX)
    assert r.status_code == 422 and Ticket.objects.count() == 0
    t = services.create_ticket(dev, company=project.company, title="Mío")
    outsider = client_for(make_user())
    assert outsider.post(f"/tickets/{t.pk}/toggle/", {}, **HX).status_code == 404


def test_requires_login_and_panel_is_in_pages(project, po, client_for):
    from tests.conftest import CsrfClient

    assert CsrfClient().get("/tickets/panel/").status_code == 302
    page = client_for(po).get("/").content
    assert b'id="tickets-aside"' in page and b'id="tickets-toggle"' in page and b"Tickets diarios" in page
    assert b'id="tickets-aside"' not in CsrfClient().get("/accounts/login/").content


def test_page_without_javascript_works(project, po, dev, client_for):
    c = client_for(po)
    r = c.post("/tickets/new/", {"title": "Sin JS", "company": project.company_id})
    assert r.status_code == 302 and r.url == "/tickets/"
    assert b"Sin JS" in c.get("/tickets/").content
