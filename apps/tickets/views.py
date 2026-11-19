from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.exceptions import ServiceError
from apps.core.htmx import is_htmx
from apps.projects.services import companies_for

from . import services
from .forms import TicketForm
from .models import Ticket


def _panel_context(request, *, ajax, message=None, level="error", form=None):
    user = request.user
    today = timezone.localdate()
    company_filter = request.GET.get("company") or request.POST.get("filter") or ""
    companies = list(companies_for(user))
    manager_ids = services.manager_company_ids(user)
    # Personas a las que puedo asignar, con las empresas (donde soy responsable) que comparten conmigo.
    assignees = {}
    for c in companies:
        if c.pk in manager_ids:
            for person in services.company_users(c):
                assignees.setdefault(person.pk, {"user": person, "companies": []})["companies"].append(str(c.pk))
    tickets = list(services.tickets_for(user, today, company_filter or None))
    pending = [t for t in tickets if t.status == Ticket.OPEN]
    done = [t for t in tickets if t.status == Ticket.DONE]
    for t in tickets:
        t.can_delete = user.pk == t.created_by_id or t.company_id in manager_ids
        t.assigned_by_other = t.created_by_id != t.assignee_id
    return {
        "ajax": ajax,
        "today": today,
        "companies": companies,
        "company_filter": company_filter,
        "manager_ids": ",".join(str(i) for i in sorted(manager_ids)),
        "assignees": [{"user": a["user"], "companies": ",".join(a["companies"])} for a in assignees.values()],
        "pending": pending,
        "done": done,
        "open_count": services.open_count(user, today),
        "form": form or TicketForm(user, initial={"date": today}),
        "message": message,
        "message_level": level,
    }


def _respond(request, *, message=None, level="error", form=None, status=200):
    if is_htmx(request):
        ctx = _panel_context(request, ajax=True, message=message, level=level, form=form)
        return render(request, "tickets/_panel.html", ctx, status=status)
    if message:
        (messages.success if level == "success" else messages.error)(request, message)
    return redirect("tickets_page")


@login_required
def panel(request):
    return render(request, "tickets/_panel.html", _panel_context(request, ajax=True))


@login_required
def page(request):
    ctx = _panel_context(request, ajax=False)
    ctx["hide_tickets_panel"] = True
    return render(request, "tickets/page.html", ctx)


@require_POST
@login_required
def ticket_new(request):
    form = TicketForm(request.user, request.POST)
    if not form.is_valid():
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        return _respond(request, message=errors, form=form, status=422)
    try:
        services.create_ticket(request.user, **form.cleaned_data)
    except ServiceError as e:
        return _respond(request, message=e.message, form=form, status=422)
    return _respond(request, message="Ticket creado.", level="success")


def _own_ticket(request, ticket_id):
    """El ticket debe ser de una empresa donde participo (si no, 404)."""
    return get_object_or_404(Ticket, pk=ticket_id, company__in=companies_for(request.user))


@require_POST
@login_required
def ticket_toggle(request, ticket_id):
    ticket = _own_ticket(request, ticket_id)
    try:
        services.toggle_ticket(ticket, request.user)
    except ServiceError as e:
        return _respond(request, message=e.message, status=422)
    return _respond(request)


@require_POST
@login_required
def ticket_delete(request, ticket_id):
    ticket = _own_ticket(request, ticket_id)
    try:
        services.delete_ticket(ticket, request.user)
    except ServiceError as e:
        return _respond(request, message=e.message, status=422)
    return _respond(request, message="Ticket borrado.", level="success")
