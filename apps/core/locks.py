from django.apps import apps
from django.db import transaction


def lock_project(project_id):
    """Toma el bloqueo de fila del proyecto. Debe llamarse dentro de una transacción."""
    Project = apps.get_model("projects", "Project")
    with transaction.atomic():
        return Project.objects.select_for_update().get(pk=project_id)
