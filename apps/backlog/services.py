from django.apps import apps
from django.db import transaction
from django.db.models import Prefetch

from apps.board.models import BoardColumn, ColumnTransition
from apps.core.exceptions import Conflict, Forbidden, Unprocessable
from apps.core.locks import lock_project
from apps.core.permissions import PO, can_move_task, role_of
from apps.sprints.models import Sprint

from .models import Comment, Milestone, SprintTask, Task, TaskDependency

EDITABLE_FIELDS = (
    "title", "description", "stakeholder", "parent", "estimate_points", "assignee", "start_date", "due_date",
)


# ---------------------------------------------------------------- hitos y tareas
def create_milestone(project, name, date):
    return Milestone.objects.create(project=project, name=name, date=date)


def _is_member(project, user):
    ProjectMember = apps.get_model("projects", "ProjectMember")
    return ProjectMember.objects.filter(project=project, user=user).exists()


def _validate_task_data(project, kind, data, task=None):
    parent, assignee = data.get("parent"), data.get("assignee")
    if parent is not None:
        if parent.project_id != project.pk:
            raise Unprocessable("La historia padre es de otro proyecto.")
        if parent.kind != Task.STORY:
            raise Unprocessable("El padre de una tarea debe ser una historia.")
        if kind == Task.STORY:
            raise Unprocessable("Una historia no puede tener padre.")
    if assignee is not None:
        keeps_old = task is not None and task.assignee_id == assignee.pk
        if not keeps_old and not _is_member(project, assignee):
            raise Unprocessable("El responsable debe ser miembro del proyecto.")
    if kind == Task.STORY and (data.get("start_date") or data.get("due_date")):
        raise Unprocessable("Una historia no tiene fechas.")


def create_task(project, *, title, kind=Task.TASK, **data):
    if kind not in (Task.STORY, Task.TASK):
        raise Unprocessable("Tipo de tarea no válido.")
    _validate_task_data(project, kind, data)
    fields = {k: v for k, v in data.items() if k in EDITABLE_FIELDS}
    return Task.objects.create(project=project, title=title, kind=kind, **fields)


def update_task(task, **data):
    """Guarda solo los campos recibidos (nunca `column`, `sprint` ni `status`)."""
    data = {k: v for k, v in data.items() if k in EDITABLE_FIELDS}
    _validate_task_data(task.project, task.kind, data, task=task)
    for key, value in data.items():
        setattr(task, key, value)
    task.save(update_fields=[*data.keys(), "updated_at"])
    return task


def delete_task(task):
    with transaction.atomic():
        lock_project(task.project_id)
        task = Task.objects.get(pk=task.pk)
        if (
            task.children.exists()
            or task.dependencies.exists()
            or task.dependents.exists()
            or task.sprint_id is not None
            or task.sprint_history.exists()
        ):
            raise Conflict("La tarea tiene hijas, dependencias, sprint o historial y no se puede borrar.")
        task.delete()


# ---------------------------------------------------------------- comentarios
def add_comment(task, author, body):
    body = (body or "").strip()
    if not body:
        raise Unprocessable("El comentario no puede estar vacío.")
    if not _is_member(task.project, author):
        raise Forbidden("Solo los miembros del proyecto pueden comentar.")
    return Comment.objects.create(task=task, author=author, body=body)


def delete_comment(comment, user):
    """Borra un comentario: solo su autor o el Product Owner."""
    if comment.author_id != user.pk and role_of(user, comment.task.project_id) != PO:
        raise Forbidden("Solo el autor o el Product Owner pueden borrar el comentario.")
    comment.delete()


# ---------------------------------------------------------------- dependencias
def _reaches(start_id, target_id):
    """True si desde `start_id` se llega a `target_id` siguiendo `depends_on` (recorrido iterativo)."""
    seen, stack = set(), [start_id]
    while stack:
        current = stack.pop()
        if current == target_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(TaskDependency.objects.filter(task_id=current).values_list("depends_on_id", flat=True))
    return False


def add_dependency(task, depends_on):
    if task.pk == depends_on.pk:
        raise Unprocessable("Una tarea no puede depender de sí misma.")
    if task.project_id != depends_on.project_id:
        raise Unprocessable("Las dos tareas deben ser del mismo proyecto.")
    if task.kind != Task.TASK or depends_on.kind != Task.TASK:
        raise Unprocessable("Las dependencias solo existen entre tareas, no entre historias.")
    if TaskDependency.objects.filter(task=task, depends_on=depends_on).exists():
        raise Unprocessable("Esa dependencia ya existe.")
    if _reaches(depends_on.pk, task.pk):
        raise Unprocessable("La dependencia cerraría un ciclo.")
    return TaskDependency.objects.create(task=task, depends_on=depends_on)


def remove_dependency(task, dependency_id):
    deleted, _ = TaskDependency.objects.filter(pk=dependency_id, task=task).delete()
    return deleted


# ---------------------------------------------------------------- colocación en sprint / columna
def apply_placement(task, sprint, column):
    """Único escritor de `sprint` y `column`. La llama quien ya tomó el bloqueo del proyecto."""
    if (sprint is None) != (column is None):
        raise Unprocessable("Sprint y columna van juntos.")
    if sprint is not None and sprint.status == Sprint.ACTIVE and column.wip_limit is not None:
        count = Task.objects.filter(sprint=sprint, column=column).exclude(pk=task.pk).count()
        if count >= column.wip_limit:
            raise Conflict(
                f"La columna «{column.name}» alcanzó su límite WIP ({count} / {column.wip_limit})."
            )
    task.sprint, task.column = sprint, column
    task.save(update_fields=["sprint", "column", "updated_at"])
    return task


def assign_sprint(task, sprint):
    with transaction.atomic():
        lock_project(task.project_id)
        task = Task.objects.get(pk=task.pk)
        sprint = Sprint.objects.get(pk=sprint.pk)
        if task.kind != Task.TASK:
            raise Unprocessable("Solo las tareas se asignan a un sprint, no las historias.")
        if task.sprint_id is not None:
            raise Unprocessable("La tarea ya tiene sprint.")
        if sprint.project_id != task.project_id:
            raise Unprocessable("El sprint es de otro proyecto.")
        if sprint.status not in (Sprint.PLANNED, Sprint.ACTIVE):
            raise Unprocessable("Solo se puede asignar a un sprint planificado o activo.")
        first = BoardColumn.objects.filter(project_id=task.project_id).first()
        if first is None:
            raise Unprocessable("El proyecto no tiene columnas.")
        return apply_placement(task, sprint, first)


def assign_story_to_sprint(story, sprint):
    """Asigna a un sprint todas las actividades de la historia que aún no tienen sprint."""
    with transaction.atomic():
        story = Task.objects.get(pk=story.pk)
        if story.kind != Task.STORY:
            raise Unprocessable("Solo una historia se asigna completa a un sprint.")
        pending = list(Task.objects.filter(parent=story, sprint__isnull=True).order_by("id"))
        if not pending:
            raise Unprocessable("La historia no tiene actividades pendientes de asignar a un sprint.")
        for task in pending:
            assign_sprint(task, sprint)  # si una falla (WIP, sprint cerrado), se revierten todas
        return pending


def move_task(task, column, user):
    with transaction.atomic():
        lock_project(task.project_id)
        task = Task.objects.select_related("sprint", "column").get(pk=task.pk)
        if not can_move_task(user, task):
            raise Forbidden("No tienes permiso para mover esta tarea.")
        try:
            column = BoardColumn.objects.get(pk=column.pk)
        except BoardColumn.DoesNotExist:
            raise Unprocessable("La columna no existe.") from None
        if (
            task.kind != Task.TASK
            or task.sprint_id is None
            or task.sprint.status != Sprint.ACTIVE
            or column.project_id != task.project_id
        ):
            raise Unprocessable("Solo se mueven tareas del sprint activo, dentro de su proyecto.")
        if task.column_id == column.pk:
            return task
        allowed = ColumnTransition.objects.filter(from_column_id=task.column_id).select_related("to_column")
        allowed_ids = {t.to_column_id for t in allowed}
        if column.pk not in allowed_ids:
            names = ", ".join(t.to_column.name for t in allowed) or "ninguna"
            raise Unprocessable(
                f"No se puede mover de «{task.column.name}» a «{column.name}». Destinos permitidos: {names}."
            )
        return apply_placement(task, task.sprint, column)


def close_sprint(sprint, review_notes="", retro_notes=""):
    with transaction.atomic():
        lock_project(sprint.project_id)
        sprint = Sprint.objects.get(pk=sprint.pk)
        if sprint.status != Sprint.ACTIVE:
            raise Conflict("Solo se puede cerrar un sprint activo.")
        tasks = list(Task.objects.filter(sprint=sprint).select_related("column"))
        SprintTask.objects.bulk_create(
            SprintTask(
                sprint=sprint,
                task=t,
                column_name=t.column.name,
                is_done=t.column.is_done,
                estimate_points=t.estimate_points,
            )
            for t in tasks
        )
        for t in tasks:
            if not t.column.is_done:
                apply_placement(t, None, None)
        sprint.status = Sprint.CLOSED
        sprint.review_notes, sprint.retro_notes = review_notes, retro_notes
        sprint.save(update_fields=["status", "review_notes", "retro_notes", "updated_at"])
        return sprint


# ---------------------------------------------------------------- tablero
def get_board(project):
    sprint = Sprint.objects.filter(project=project, status=Sprint.ACTIVE).first()
    columns = list(BoardColumn.objects.filter(project=project))
    by_id = {c.pk: c for c in columns}
    transitions = {}
    for t in ColumnTransition.objects.filter(from_column__project=project):
        transitions.setdefault(t.from_column_id, []).append(t.to_column_id)
    rows = {c.pk: [] for c in columns}
    if sprint is not None:
        comments = Comment.objects.select_related("author")
        tasks = (
            Task.objects.filter(sprint=sprint)
            .select_related("assignee")
            .prefetch_related(Prefetch("comments", queryset=comments))
            .order_by("id")
        )
        for t in tasks:
            everything = list(t.comments.all())
            t.comment_count = len(everything)
            t.recent_comments = everything[-3:]
            t.allowed = [by_id[i] for i in transitions.get(t.column_id, [])]
            t.allowed_ids = " ".join(str(c.pk) for c in t.allowed)
            rows[t.column_id].append(t)
    return {
        "sprint": sprint,
        "columns": [
            {
                "column": c,
                "tasks": rows[c.pk],
                "count": len(rows[c.pk]),
                "full": c.wip_limit is not None and len(rows[c.pk]) >= c.wip_limit,
            }
            for c in columns
        ],
    }
