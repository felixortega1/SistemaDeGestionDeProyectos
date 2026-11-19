from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.backlog import services as backlog_services
from apps.backlog.models import Task
from apps.core.exceptions import Unprocessable
from apps.core.permissions import ANY_ROLE, SM_UP, from_sprint_id, project_role_required

from . import services
from .forms import CloseSprintForm, SprintForm
from .models import Sprint


def _page(request, new_form=None, status=200):
    project = request.project
    sprints = list(project.sprints.all())
    tasks = Task.objects.filter(project=project, kind="task").select_related("column", "assignee").order_by("id")
    by_sprint = {}
    backlog_tasks = []
    for t in tasks:
        if t.sprint_id:
            by_sprint.setdefault(t.sprint_id, []).append(t)
        else:
            backlog_tasks.append(t)
    for s in sprints:
        s.task_list = by_sprint.get(s.pk, [])
        s.edit_form = SprintForm(initial={
            "name": s.name, "goal": s.goal, "start_date": s.start_date, "end_date": s.end_date,
        })
    pending_stories = [
        st for st in Task.objects.filter(project=project, kind="story").order_by("id")
        if st.children.filter(sprint__isnull=True).exists()
    ]
    ctx = {
        "project": project,
        "pending_stories": pending_stories,
        "sprints": sprints,
        "backlog_tasks": backlog_tasks,
        "new_form": new_form or SprintForm(),
        "close_form": CloseSprintForm(),
        "can_manage": request.member.role in SM_UP,
        "nav": "sprints",
    }
    return render(request, "sprints/sprints.html", ctx, status=status)


@project_role_required(ANY_ROLE)
def sprints(request, project_id):
    return _page(request)


@require_POST
@project_role_required(SM_UP)
def sprint_new(request, project_id):
    form = SprintForm(request.POST)
    if form.is_valid():
        try:
            services.create_sprint(request.project, **form.cleaned_data)
            return redirect("sprints", project_id=project_id)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _page(request, form, 422)


@require_POST
@project_role_required(SM_UP, from_sprint_id)
def sprint_edit(request, sprint_id):
    form = SprintForm(request.POST)
    if form.is_valid():
        try:
            services.update_sprint(request.obj, **form.cleaned_data)
            return redirect("sprints", project_id=request.project.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _page_with_errors(request, form)


def _page_with_errors(request, form):
    messages.error(request, "; ".join(m for errs in form.errors.values() for m in errs))
    return _page(request, None, 422)


@require_POST
@project_role_required(SM_UP, from_sprint_id)
def sprint_start(request, sprint_id):
    services.start_sprint(request.obj)
    messages.success(request, "Sprint iniciado.")
    return redirect("sprints", project_id=request.project.pk)


@require_POST
@project_role_required(SM_UP, from_sprint_id)
def sprint_close(request, sprint_id):
    form = CloseSprintForm(request.POST)
    notes = form.cleaned_data if form.is_valid() else {}
    backlog_services.close_sprint(request.obj, notes.get("review_notes", ""), notes.get("retro_notes", ""))
    messages.success(request, "Sprint cerrado. Las tareas sin terminar volvieron al backlog.")
    return redirect("sprints", project_id=request.project.pk)


__all__ = ["Sprint"]
