from decimal import Decimal

from apps.budget.models import Department
from apps.projects import services as project_services


def post_dept(client, project, name="Marketing", amount="1500", currency="USD"):
    return client.post(
        f"/projects/{project.pk}/departments/new/", {"name": name, "budget_amount": amount, "currency": currency}
    )


def test_create_department(project, po, client_for):
    r = post_dept(client_for(po), project)
    assert r.status_code == 302
    d = Department.objects.get()
    assert d.budget_amount == Decimal("1500") and d.currency == "USD" and d.updated_by == po


def test_invalid_amount_and_currency_are_422(project, po, client_for):
    c = client_for(po)
    assert post_dept(c, project, amount="-5").status_code == 422
    assert post_dept(c, project, currency="usd").status_code == 422
    assert post_dept(c, project, currency="US").status_code == 422
    assert Department.objects.count() == 0


def test_duplicate_name_is_422_but_allowed_in_other_project(project, po, client_for):
    c = client_for(po)
    post_dept(c, project)
    assert post_dept(c, project).status_code == 422
    other = project_services.create_project(po, "B")
    assert post_dept(c, other).status_code == 302


def test_edit_updates_updated_by(project, po, sm, client_for):
    post_dept(client_for(po), project)
    d = Department.objects.get()
    r = client_for(sm).post(
        f"/departments/{d.pk}/edit/", {"name": "Marketing", "budget_amount": "2000", "currency": "EUR"}
    )
    assert r.status_code == 302
    d.refresh_from_db()
    assert d.budget_amount == 2000 and d.updated_by == sm


def test_developer_cannot_edit_but_can_read(project, po, dev, client_for):
    post_dept(client_for(po), project)
    c = client_for(dev)
    assert c.get(f"/projects/{project.pk}/budget/").status_code == 200
    assert post_dept(c, project, name="X").status_code == 403
