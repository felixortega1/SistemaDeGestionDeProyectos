from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.core.exceptions import Forbidden, Unprocessable
from apps.core.permissions import SM_UP
from apps.projects.models import ProjectMember
from apps.projects.services import companies_for

from .models import Ticket


def manager_company_ids(user):
    """Empresas donde el usuario es Product Owner, Project Manager o Scrum Master de algún proyecto."""
    ids = ProjectMember.objects.filter(user=user, role__in=SM_UP).values_list("project__company_id", flat=True)
    return set(ids)


def company_users(company):
    """Personas que participan en algún proyecto de la empresa."""
    return get_user_model().objects.filter(memberships__project__company=company).distinct().order_by("name", "email")


def create_ticket(user, *, company, title, description="", date=None, assignee=None):
    title = (title or "").strip()
    if not title:
        raise Unprocessable("El ticket necesita un título.")
    if not companies_for(user).filter(pk=company.pk).exists():
        raise Unprocessable("Solo puedes crear tickets en las empresas donde participas.")
    assignee = assignee or user
    if assignee.pk != user.pk:
        if company.pk not in manager_company_ids(user):
            raise Forbidden(
                "Solo el Product Owner, el Project Manager o el Scrum Master de la empresa "
                "pueden asignar tickets a otras personas."
            )
        if not company_users(company).filter(pk=assignee.pk).exists():
            raise Unprocessable("Esa persona no participa en la empresa.")
    return Ticket.objects.create(
        company=company,
        title=title,
        description=description or "",
        date=date or timezone.localdate(),
        created_by=user,
        assignee=assignee,
    )


def _can_touch(user, ticket):
    return user.pk in (ticket.assignee_id, ticket.created_by_id)


def toggle_ticket(ticket, user):
    """Marca el ticket como hecho o lo reabre. Lo hace quien lo tiene asignado o quien lo creó."""
    if not _can_touch(user, ticket):
        raise Forbidden("Solo la persona asignada o quien creó el ticket puede cambiar su estado.")
    if ticket.status == Ticket.OPEN:
        ticket.status, ticket.done_at = Ticket.DONE, timezone.now()
    else:
        ticket.status, ticket.done_at = Ticket.OPEN, None
    ticket.save(update_fields=["status", "done_at"])
    return ticket


def delete_ticket(ticket, user):
    """Borra el ticket: quien lo creó o un responsable (PO, PM o SM) de la empresa."""
    if user.pk != ticket.created_by_id and ticket.company_id not in manager_company_ids(user):
        raise Forbidden("Solo quien creó el ticket o un responsable de la empresa puede borrarlo.")
    ticket.delete()


def tickets_for(user, today=None, company_id=None):
    """Tickets del usuario: los de hoy (hechos o no) y los pendientes de días anteriores."""
    today = today or timezone.localdate()
    qs = Ticket.objects.filter(assignee=user).filter(Q(date=today) | Q(date__lt=today, status=Ticket.OPEN))
    if company_id:
        qs = qs.filter(company_id=company_id)
    return qs.select_related("company", "created_by").order_by("status", "date", "id")


def open_count(user, today=None):
    today = today or timezone.localdate()
    return Ticket.objects.filter(assignee=user, status=Ticket.OPEN, date__lte=today).count()
