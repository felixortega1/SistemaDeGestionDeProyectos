from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.backlog import services as backlog_services
from apps.backlog.forms import CommentForm
from apps.backlog.models import Task
from apps.core.exceptions import Conflict, Unprocessable
from apps.core.htmx import is_htmx
from apps.core.permissions import ANY_ROLE, SM_UP, from_column_id, from_task_id, project_role_required

from . import services
from .forms import ColumnForm, MoveForm
from .models import BoardColumn, ColumnTransition


def _board_context(request, project, message=None, level="error", open_task=None):
    ctx = {"project": project, "message": message, "message_level": level, "open_task": open_task, "nav": "board"}
    ctx.update(backlog_services.get_board(project))
    return ctx


@project_role_required(ANY_ROLE)
def board(request, project_id):
    return render(request, "board/board.html", _board_context(request, request.project))


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def task_move(request, task_id):
    project = request.project
    form = MoveForm(request.POST)
    status, message = 200, None
    if not form.is_valid():
        status, message = 422, "Falta la columna de destino."
    else:
        column = BoardColumn.objects.filter(pk=form.cleaned_data["column_id"]).first()
        try:
            if column is None:
                raise Unprocessable("La columna no existe.")
            backlog_services.move_task(request.obj, column, request.user)
        except (Conflict, Unprocessable) as e:
            status, message = e.status, e.message
    if is_htmx(request):
        return render(
            request, "board/_board.html", _board_context(request, project, message), status=status
        )
    if message:
        messages.error(request, message)
    return redirect("board", project_id=project.pk)


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def board_comment(request, task_id):
    """Comentario rápido desde una tarjeta del Kanban."""
    form = CommentForm(request.POST)
    if form.is_valid():
        backlog_services.add_comment(request.obj, request.user, form.cleaned_data["body"])
        status, message, level = 200, "Comentario guardado.", "success"
    else:
        status, message, level = 422, "El comentario no puede estar vacío.", "error"
    if is_htmx(request):
        ctx = _board_context(request, request.project, message, level, open_task=request.obj.pk)
        return render(request, "board/_board.html", ctx, status=status)
    (messages.success if level == "success" else messages.error)(request, message)
    return redirect("board", project_id=request.project.pk)


# ---------------------------------------------------------------- columnas y transiciones
def _columns_page(request, new_form=None, status=200, edit_errors=None):
    project = request.project
    columns = list(BoardColumn.objects.filter(project=project))
    existing = set(ColumnTransition.objects.filter(from_column__project=project).values_list("from_column_id", "to_column_id"))
    for c in columns:
        c.form = ColumnForm(initial={"name": c.name, "wip_limit": c.wip_limit, "policy_text": c.policy_text})
        c.matrix = [(o, (c.pk, o.pk) in existing) for o in columns if o.pk != c.pk]
    ctx = {
        "project": project,
        "columns": columns,
        "new_form": new_form or ColumnForm(),
        "nav": "columns",
    }
    return render(request, "board/columns.html", ctx, status=status)


@project_role_required(SM_UP)
def columns(request, project_id):
    return _columns_page(request)


@require_POST
@project_role_required(SM_UP)
def column_new(request, project_id):
    form = ColumnForm(request.POST)
    if form.is_valid():
        services.create_column(request.project, **form.cleaned_data)
        return redirect("columns", project_id=project_id)
    return _columns_page(request, form, 422)


@require_POST
@project_role_required(SM_UP, from_column_id)
def column_edit(request, column_id):
    form = ColumnForm(request.POST)
    if not form.is_valid():
        messages.error(request, "; ".join(m for errs in form.errors.values() for m in errs))
        return _columns_page(request, None, 422)
    services.update_column(request.obj, **form.cleaned_data)
    return redirect("columns", project_id=request.project.pk)


@require_POST
@project_role_required(SM_UP)
def transitions(request, project_id):
    pairs = []
    for value in request.POST.getlist("transition"):
        try:
            a, b = value.split("_")
            pairs.append((int(a), int(b)))
        except ValueError:
            raise Unprocessable("Transición no válida.") from None
    services.set_transitions(request.project, pairs)
    messages.success(request, "Transiciones guardadas.")
    return redirect("columns", project_id=project_id)


__all__ = ["Task"]
