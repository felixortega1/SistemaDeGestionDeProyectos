import re

from django.apps import apps
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Prefetch, Q, Value, When

from apps.board.models import BoardColumn, ColumnTransition
from apps.core.exceptions import Conflict, Forbidden, Unprocessable
from apps.core.locks import lock_project
from apps.core.permissions import PO, can_move_task, role_of
from apps.sprints.models import Sprint

from .models import AcceptanceCriterion, Comment, Epic, Milestone, SprintTask, Story, Task, TaskDependency

STORY_FIELDS = ("title", "description", "stakeholder", "epic", "priority", "estimate_points")
TASK_FIELDS = ("title", "description", "story", "estimate_points", "assignee", "start_date", "due_date")
EDITABLE_FIELDS = TASK_FIELDS  # nombre histórico: los campos editables de una tarea
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
PRIORITIES = {value for value, _ in Story.PRIORITIES}


def order_by_priority(queryset):
    """Ordena historias por prioridad (alta, media, baja) y luego por id."""
    rank = Case(
        When(priority=Story.HIGH, then=Value(0)),
        When(priority=Story.MEDIUM, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    return queryset.annotate(priority_rank=rank).order_by("priority_rank", "id")


def _is_member(project, user):
    ProjectMember = apps.get_model("projects", "ProjectMember")
    return ProjectMember.objects.filter(project=project, user=user).exists()


# ---------------------------------------------------------------- hitos
def create_milestone(project, name, date):
    return Milestone.objects.create(project=project, name=name, date=date)


# ---------------------------------------------------------------- historias
def _validate_story_data(project, data):
    epic = data.get("epic")
    if epic is not None and epic.project_id != project.pk:
        raise Unprocessable("La épica es de otro proyecto.")
    if "priority" in data and data["priority"] not in PRIORITIES:
        raise Unprocessable("Prioridad no válida.")
    if not (data.get("title", "x") or "").strip():
        raise Unprocessable("La historia necesita un título.")


def create_story(project, *, title, **data):
    data = {k: v for k, v in data.items() if k in STORY_FIELDS}
    _validate_story_data(project, {"title": title, **data})
    return Story.objects.create(project=project, title=title.strip(), **data)


def update_story(story, **data):
    """Guarda solo los campos recibidos."""
    data = {k: v for k, v in data.items() if k in STORY_FIELDS}
    _validate_story_data(story.project, data)
    for key, value in data.items():
        setattr(story, key, value)
    story.save(update_fields=[*data.keys(), "updated_at"])
    return story


def delete_story(story):
    with transaction.atomic():
        lock_project(story.project_id)
        story = Story.objects.get(pk=story.pk)
        if story.tasks.exists():
            raise Conflict("La historia tiene tareas y no se puede borrar.")
        story.delete()  # los criterios y comentarios se borran en cascada


# ---------------------------------------------------------------- tareas
def _validate_task_data(project, data, task=None):
    story, assignee = data.get("story"), data.get("assignee")
    if story is not None and story.project_id != project.pk:
        raise Unprocessable("La historia es de otro proyecto.")
    if assignee is not None:
        keeps_old = task is not None and task.assignee_id == assignee.pk
        if not keeps_old and not _is_member(project, assignee):
            raise Unprocessable("El responsable debe ser miembro del proyecto.")


def create_task(project, *, title, **data):
    data = {k: v for k, v in data.items() if k in TASK_FIELDS}
    _validate_task_data(project, data)
    return Task.objects.create(project=project, title=title, **data)


def update_task(task, **data):
    """Guarda solo los campos recibidos (nunca `column` ni `sprint`)."""
    data = {k: v for k, v in data.items() if k in TASK_FIELDS}
    _validate_task_data(task.project, data, task=task)
    for key, value in data.items():
        setattr(task, key, value)
    task.save(update_fields=[*data.keys(), "updated_at"])
    return task


def delete_task(task):
    with transaction.atomic():
        lock_project(task.project_id)
        task = Task.objects.get(pk=task.pk)
        if (
            task.dependencies.exists()
            or task.dependents.exists()
            or task.sprint_id is not None
            or task.sprint_history.exists()
        ):
            raise Conflict("La tarea tiene dependencias, sprint o historial y no se puede borrar.")
        task.delete()


# ---------------------------------------------------------------- épicas
def _check_epic(title, color):
    if not (title or "").strip():
        raise Unprocessable("La épica necesita un título.")
    if not HEX_COLOR_RE.match(color or ""):
        raise Unprocessable("El color debe tener el formato #RRGGBB.")


def create_epic(project, *, title, description="", color=Epic.DEFAULT_COLOR):
    title = (title or "").strip()
    _check_epic(title, color)
    return Epic.objects.create(project=project, title=title, description=description or "", color=color.upper())


def update_epic(epic, *, title, description="", color=Epic.DEFAULT_COLOR):
    title = (title or "").strip()
    _check_epic(title, color)
    epic.title, epic.description, epic.color = title, description or "", color.upper()
    epic.save(update_fields=["title", "description", "color"])
    return epic


def delete_epic(epic):
    with transaction.atomic():
        epic = Epic.objects.select_for_update().get(pk=epic.pk)
        if Story.objects.filter(epic=epic).exists():
            raise Conflict("La épica tiene historias asociadas y no se puede borrar.")
        epic.delete()


# ---------------------------------------------------------------- criterios de aceptación
def add_criterion(story, text):
    text = (text or "").strip()
    if not text:
        raise Unprocessable("El criterio no puede estar vacío.")
    if len(text) > 500:
        raise Unprocessable("El criterio debe tener 500 caracteres o menos.")
    last = story.criteria.order_by("-position").values_list("position", flat=True).first()
    return AcceptanceCriterion.objects.create(story=story, text=text, position=(last + 1) if last is not None else 0)


def toggle_criterion(criterion, user):
    if not _is_member(criterion.story.project, user):
        raise Forbidden("Solo los miembros del proyecto pueden marcar criterios.")
    criterion.is_done = not criterion.is_done
    criterion.save(update_fields=["is_done"])
    return criterion


def delete_criterion(criterion):
    criterion.delete()


def criteria_counts(project):
    """{id de historia: (cumplidos, total)} de los criterios de todas las historias del proyecto."""
    rows = (
        AcceptanceCriterion.objects.filter(story__project=project)
        .order_by()
        .values("story_id")
        .annotate(total=Count("id"), done=Count("id", filter=Q(is_done=True)))
    )
    return {row["story_id"]: (row["done"], row["total"]) for row in rows}


def criteria_progress(story):
    """Devuelve (cumplidos, total) de los criterios de una historia."""
    total = story.criteria.count()
    return story.criteria.filter(is_done=True).count(), total


# ---------------------------------------------------------------- comentarios
def add_comment(target, author, body):
    """Comenta una historia o una tarea (`target`). Solo los miembros del proyecto."""
    body = (body or "").strip()
    if not body:
        raise Unprocessable("El comentario no puede estar vacío.")
    if not _is_member(target.project, author):
        raise Forbidden("Solo los miembros del proyecto pueden comentar.")
    field = "story" if isinstance(target, Story) else "task"
    return Comment.objects.create(**{field: target}, author=author, body=body)


def delete_comment(comment, user):
    """Borra un comentario: solo su autor o el Product Owner."""
    if comment.author_id != user.pk and role_of(user, comment.project.pk) != PO:
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
    """Asigna a un sprint todas las tareas de la historia que aún no tienen sprint."""
    with transaction.atomic():
        story = Story.objects.get(pk=story.pk)
        pending = list(Task.objects.filter(story=story, sprint__isnull=True).order_by("id"))
        if not pending:
            raise Unprocessable("La historia no tiene tareas pendientes de asignar a un sprint.")
        for task in pending:
            assign_sprint(task, sprint)  # si una falla (WIP, sprint cerrado), se revierten todas
        return pending


def unassign_sprint(task):
    """Devuelve una tarea de un sprint planificado al backlog."""
    with transaction.atomic():
        lock_project(task.project_id)
        task = Task.objects.select_related("sprint").get(pk=task.pk)
        if task.sprint_id is None:
            raise Unprocessable("La tarea no tiene sprint.")
        if task.sprint.status != Sprint.PLANNED:
            raise Conflict("Solo se puede devolver al backlog una tarea de un sprint planificado.")
        return apply_placement(task, None, None)


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
        if task.sprint_id is None or task.sprint.status != Sprint.ACTIVE or column.project_id != task.project_id:
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


# ---------------------------------------------------------------- métricas de sprint
def _percent(done, total):
    return round(100 * done / total) if total else 0


def sprint_metrics(project):
    """Métricas Scrum por sprint del proyecto y velocidad promedio. Solo lee.

    Devuelve ({sprint_id: dict}, velocidad). Para sprints planificados o activos: puntos y tareas
    totales/hechas y porcentaje. Para cerrados: puntos comprometidos y completados según `SprintTask`.
    La velocidad es el promedio de puntos completados de los sprints cerrados (None si no hay ninguno)."""
    result = {}
    open_tasks = Task.objects.filter(
        project=project, sprint__status__in=[Sprint.PLANNED, Sprint.ACTIVE]
    ).select_related("column")
    for t in open_tasks:
        m = result.setdefault(t.sprint_id, {"total_points": 0, "done_points": 0, "total_tasks": 0, "done_tasks": 0})
        points = t.estimate_points or 0
        m["total_points"] += points
        m["total_tasks"] += 1
        if t.column is not None and t.column.is_done:
            m["done_points"] += points
            m["done_tasks"] += 1
    for m in result.values():
        if m["total_points"]:
            m["percent"] = _percent(m["done_points"], m["total_points"])
        else:  # sin estimaciones: el avance se mide por cantidad de tareas
            m["percent"] = _percent(m["done_tasks"], m["total_tasks"])

    completed = []
    for sprint in Sprint.objects.filter(project=project, status=Sprint.CLOSED):
        rows = list(SprintTask.objects.filter(sprint=sprint))
        committed = sum(r.estimate_points or 0 for r in rows)
        done = sum(r.estimate_points or 0 for r in rows if r.is_done)
        result[sprint.pk] = {
            "committed_points": committed,
            "completed_points": done,
            "total_tasks": len(rows),
            "done_tasks": sum(1 for r in rows if r.is_done),
            "percent": _percent(done, committed),
        }
        completed.append(done)
    velocity = round(sum(completed) / len(completed), 1) if completed else None
    return result, velocity


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
        tasks = list(
            Task.objects.filter(sprint=sprint)
            .select_related("assignee", "story", "story__epic")
            .prefetch_related(Prefetch("comments", queryset=comments))
            .order_by("id")
        )
        story_ids = {t.story_id for t in tasks if t.story_id}
        progress = {
            row["story_id"]: (row["done"], row["total"])
            for row in AcceptanceCriterion.objects.filter(story_id__in=story_ids)
            .order_by()
            .values("story_id")
            .annotate(total=Count("id"), done=Count("id", filter=Q(is_done=True)))
        }
        for t in tasks:
            t.story_criteria = progress.get(t.story_id)
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
