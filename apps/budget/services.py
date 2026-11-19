import re
from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.core.exceptions import Conflict, Unprocessable

from .models import Department

CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def _validate(amount, currency):
    if Decimal(amount) < 0:
        raise Unprocessable("El monto no puede ser negativo.")
    if not CURRENCY_RE.match(currency or ""):
        raise Unprocessable("La moneda debe ser un código de tres letras mayúsculas (por ejemplo USD).")


def _name_taken(project, name, exclude_pk=None):
    qs = Department.objects.filter(project=project, name=name)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def create_department(project, user, name, budget_amount, currency):
    _validate(budget_amount, currency)
    if _name_taken(project, name):
        raise Unprocessable("Ya existe un departamento con ese nombre en el proyecto.")
    try:
        with transaction.atomic():
            return Department.objects.create(
                project=project, name=name, budget_amount=budget_amount, currency=currency, updated_by=user
            )
    except IntegrityError:
        raise Conflict("Ya existe un departamento con ese nombre en el proyecto.") from None


def update_department(department, user, name, budget_amount, currency):
    _validate(budget_amount, currency)
    if _name_taken(department.project, name, department.pk):
        raise Unprocessable("Ya existe un departamento con ese nombre en el proyecto.")
    department.name, department.budget_amount, department.currency = name, budget_amount, currency
    department.updated_by = user
    try:
        with transaction.atomic():
            department.save()
    except IntegrityError:
        raise Conflict("Ya existe un departamento con ese nombre en el proyecto.") from None
    return department


def delete_department(department):
    department.delete()
