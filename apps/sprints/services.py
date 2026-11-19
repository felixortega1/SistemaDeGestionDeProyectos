from django.db import IntegrityError, transaction

from apps.core.exceptions import Conflict, Unprocessable
from apps.core.locks import lock_project

from .models import Sprint


def _check_dates(start_date, end_date):
    if start_date and end_date and end_date < start_date:
        raise Unprocessable("La fecha de fin no puede ser anterior a la de inicio.")


def create_sprint(project, name, goal="", start_date=None, end_date=None):
    _check_dates(start_date, end_date)
    return Sprint.objects.create(
        project=project, name=name, goal=goal, start_date=start_date, end_date=end_date
    )


def update_sprint(sprint, name, goal, start_date, end_date):
    _check_dates(start_date, end_date)
    if sprint.status == Sprint.CLOSED:
        raise Conflict("Un sprint cerrado no se puede editar.")
    sprint.name, sprint.goal = name, goal
    sprint.start_date, sprint.end_date = start_date, end_date
    sprint.save(update_fields=["name", "goal", "start_date", "end_date", "updated_at"])
    return sprint


def start_sprint(sprint):
    with transaction.atomic():
        lock_project(sprint.project_id)
        sprint = Sprint.objects.get(pk=sprint.pk)
        if sprint.status != Sprint.PLANNED:
            raise Conflict("Solo se puede iniciar un sprint planificado.")
        if not (sprint.start_date and sprint.end_date):
            raise Unprocessable("El sprint necesita fecha de inicio y de fin para empezar.")
        if Sprint.objects.filter(project_id=sprint.project_id, status=Sprint.ACTIVE).exists():
            raise Conflict("El proyecto ya tiene un sprint activo.")
        sprint.status = Sprint.ACTIVE
        try:
            with transaction.atomic():
                sprint.save(update_fields=["status", "updated_at"])
        except IntegrityError:
            raise Conflict("El proyecto ya tiene un sprint activo.") from None
    return sprint
