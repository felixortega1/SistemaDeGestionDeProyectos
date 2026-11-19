from django.db import transaction

from apps.core.exceptions import Unprocessable
from apps.core.locks import lock_project

from .models import BoardColumn, ColumnTransition

DEFAULT_COLUMNS = [
    ("Por hacer", None, "Trabajo listo para empezar.", False),
    ("En desarrollo", 3, "Máximo 3 tareas a la vez.", False),
    ("En revisión", None, "Esperando revisión.", False),
    ("Hecho", None, "Terminado según la definición de hecho.", True),
]


@transaction.atomic
def create_default_board(project):
    columns = [
        BoardColumn.objects.create(
            project=project, name=name, position=i, wip_limit=wip, policy_text=policy, is_done=done
        )
        for i, (name, wip, policy, done) in enumerate(DEFAULT_COLUMNS, start=1)
    ]
    for a, b in zip(columns, columns[1:]):
        ColumnTransition.objects.create(from_column=a, to_column=b)
        ColumnTransition.objects.create(from_column=b, to_column=a)
    return columns


@transaction.atomic
def create_column(project, name, wip_limit=None, policy_text=""):
    lock_project(project.pk)
    done = BoardColumn.objects.filter(project=project, is_done=True).first()
    if done is None:
        raise Unprocessable("El proyecto no tiene columna de terminadas.")
    previous = BoardColumn.objects.filter(project=project, position__lt=done.position).last()
    position = done.position
    done.position += 1
    done.save(update_fields=["position"])
    column = BoardColumn.objects.create(
        project=project, name=name, position=position, wip_limit=wip_limit, policy_text=policy_text
    )
    if previous is not None:
        ColumnTransition.objects.create(from_column=previous, to_column=column)
        ColumnTransition.objects.create(from_column=column, to_column=previous)
    ColumnTransition.objects.create(from_column=column, to_column=done)
    ColumnTransition.objects.create(from_column=done, to_column=column)
    return column


def update_column(column, name, wip_limit, policy_text):
    column.name, column.wip_limit, column.policy_text = name, wip_limit, policy_text
    column.save(update_fields=["name", "wip_limit", "policy_text"])
    return column


@transaction.atomic
def set_transitions(project, pairs):
    """Reemplaza todas las transiciones del proyecto. `pairs` es un iterable de (from_id, to_id)."""
    ids = set(BoardColumn.objects.filter(project=project).values_list("id", flat=True))
    pairs = set(pairs)
    for a, b in pairs:
        if a not in ids or b not in ids:
            raise Unprocessable("Una de las columnas no pertenece al proyecto.")
        if a == b:
            raise Unprocessable("Una columna no puede tener una transición a sí misma.")
    ColumnTransition.objects.filter(from_column__project=project).delete()
    ColumnTransition.objects.bulk_create(ColumnTransition(from_column_id=a, to_column_id=b) for a, b in pairs)
