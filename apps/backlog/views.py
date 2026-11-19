from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.exceptions import Unprocessable
from apps.core.htmx import redirect_back
from apps.core.permissions import (
    ANY_ROLE,
    PM,
    PO,
    PO_ONLY,
    SM,
    SM_UP,
    STORY_CREATORS,
    can_edit_task,
    from_comment_id,
    from_task_id,
    project_role_required,
)
from apps.sprints.models import Sprint

from . import services
from .forms import (
    ASSIGNEE_ONLY,
    FULL,
    NO_ASSIGNEE,
    ActivityForm,
    AssignSprintForm,
    CommentForm,
    DependencyForm,
    MilestoneForm,
    StoryForm,
    TaskForm,
)
from .models import Task


def _backlog_page(request, status=200, task_form=None, milestone_form=None):
    project = request.project
    tasks = Task.objects.filter(project=project).select_related("sprint", "assignee", "parent").order_by("id")
    stories = [t for t in tasks if t.kind == Task.STORY]
    children = {}
    for t in tasks:
        if t.parent_id:
            children.setdefault(t.parent_id, []).append(t)
    for s in stories:
        s.child_list = children.get(s.pk, [])
    ctx = {
        "project": project,
        "stories": stories,
        "backlog_tasks": [t for t in tasks if t.kind == Task.TASK and t.sprint_id is None],
        "sprint_tasks": [t for t in tasks if t.kind == Task.TASK and t.sprint_id is not None],
        "milestones": project.milestones.all(),
        "open_sprints": project.sprints.filter(status__in=[Sprint.PLANNED, Sprint.ACTIVE]),
        "task_form": task_form or TaskForm(project),
        "milestone_form": milestone_form or MilestoneForm(),
        "is_po": request.member.role == PO,
        "can_assign_sprint": request.member.role in SM_UP,
        "nav": "backlog",
    }
    return render(request, "backlog/backlog.html", ctx, status=status)


@project_role_required(ANY_ROLE)
def backlog(request, project_id):
    return _backlog_page(request)


@require_POST
@project_role_required(PO_ONLY)
def task_new(request, project_id):
    form = TaskForm(request.project, request.POST)
    if form.is_valid():
        try:
            services.create_task(request.project, **form.cleaned_data)
            return redirect("backlog", project_id=project_id)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _backlog_page(request, 422, task_form=form)


@require_POST
@project_role_required(PO_ONLY)
def milestone_new(request, project_id):
    form = MilestoneForm(request.POST)
    if form.is_valid():
        services.create_milestone(request.project, **form.cleaned_data)
        return redirect("backlog", project_id=project_id)
    return _backlog_page(request, 422, milestone_form=form)


def _edit_mode(request, task):
    role = request.member.role
    if role == PO:
        return FULL
    if role in (SM, PM):
        return ASSIGNEE_ONLY
    if can_edit_task(request.user, task):
        return NO_ASSIGNEE
    raise PermissionDenied


def _task_page(request, task, form, dep_form=None, status=200, mode=FULL):
    ctx = {
        "project": request.project,
        "task": task,
        "form": form,
        "dep_form": dep_form or DependencyForm(task),
        "dependencies": task.dependencies.select_related("depends_on"),
        "can_edit_deps": can_edit_task(request.user, task),
        "mode": mode,
        "nav": "backlog",
    }
    return render(request, "backlog/task_form.html", ctx, status=status)


@project_role_required(ANY_ROLE, from_task_id)
def task_edit(request, task_id):
    task = request.obj
    mode = _edit_mode(request, task)
    initial = {f: getattr(task, f) for f in services.EDITABLE_FIELDS}
    if request.method == "POST":
        form = TaskForm(request.project, request.POST, mode=mode, task=task)
        if form.is_valid():
            try:
                services.update_task(task, **form.cleaned_data)
                return redirect("backlog", project_id=request.project.pk)
            except Unprocessable as e:
                form.add_error(None, e.message)
        return _task_page(request, task, form, status=422, mode=mode)
    form = TaskForm(request.project, initial=initial, mode=mode, task=task)
    return _task_page(request, task, form, mode=mode)


@require_POST
@project_role_required(PO_ONLY, from_task_id)
def task_delete(request, task_id):
    services.delete_task(request.obj)
    return redirect("backlog", project_id=request.project.pk)


@require_POST
@project_role_required(SM_UP, from_task_id)
def task_assign_sprint(request, task_id):
    form = AssignSprintForm(request.POST)
    if not form.is_valid():
        raise Unprocessable("Sprint no válido.")
    sprint = get_object_or_404(Sprint, pk=form.cleaned_data["sprint_id"], project=request.project)
    services.assign_sprint(request.obj, sprint)
    return redirect_back(request, f"/projects/{request.project.pk}/backlog/")


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def dependency_add(request, task_id):
    task = request.obj
    if not can_edit_task(request.user, task):
        raise PermissionDenied
    form = DependencyForm(task, request.POST)
    if form.is_valid():
        try:
            services.add_dependency(task, form.cleaned_data["depends_on"])
            return redirect("task_edit", task_id=task.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    edit_form = TaskForm(
        request.project, initial={f: getattr(task, f) for f in services.EDITABLE_FIELDS},
        mode=_edit_mode(request, task), task=task,
    )
    return _task_page(request, task, edit_form, dep_form=form, status=422, mode=_edit_mode(request, task))


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def dependency_delete(request, task_id, dep_id):
    if not can_edit_task(request.user, request.obj):
        raise PermissionDenied
    services.remove_dependency(request.obj, dep_id)
    return redirect("task_edit", task_id=request.obj.pk)


# ---------------------------------------------------------------- historias, detalle y comentarios
def _story_rows(project):
    tasks = list(Task.objects.filter(project=project, kind=Task.TASK).select_related("column", "sprint"))
    stories = list(Task.objects.filter(project=project, kind=Task.STORY).order_by("id"))
    for st in stories:
        mine = [t for t in tasks if t.parent_id == st.pk]
        st.total = len(mine)
        st.done = sum(1 for t in mine if t.column_id and t.column.is_done)
        st.percent = round(100 * st.done / st.total) if st.total else 0
        st.unassigned = sum(1 for t in mine if t.sprint_id is None)
    return stories, sum(1 for t in tasks if t.parent_id is None)


def _product_owner(project):
    member = project.members.filter(role=PO).select_related("user").first()
    return member.user if member else None


def _stories_page(request, form=None, status=200):
    stories, loose = _story_rows(request.project)
    ctx = {
        "project": request.project,
        "stories": stories,
        "loose_count": loose,
        "story_form": form or StoryForm(),
        "is_po": request.member.role == PO,
        "can_create": request.member.role in SM_UP,
        "product_owner": _product_owner(request.project),
        "nav": "stories",
    }
    return render(request, "backlog/stories.html", ctx, status=status)


@project_role_required(ANY_ROLE)
def stories(request, project_id):
    return _stories_page(request)


@require_POST
@project_role_required(STORY_CREATORS)
def story_new(request, project_id):
    form = StoryForm(request.POST)
    if form.is_valid():
        story = services.create_task(request.project, kind=Task.STORY, **form.cleaned_data)
        return redirect("task_detail", task_id=story.pk)
    return _stories_page(request, form, 422)


def _detail_page(request, task, comment_form=None, activity_form=None, status=200):
    project = request.project
    children = []
    if task.kind == Task.STORY:
        children = list(task.children.select_related("column", "sprint", "assignee").order_by("id"))
    role = request.member.role
    ctx = {
        "project": project,
        "task": task,
        "children": children,
        "comments": task.comments.select_related("author"),
        "comment_form": comment_form or CommentForm(),
        "activity_form": activity_form or ActivityForm(project),
        "dependencies": task.dependencies.select_related("depends_on") if task.kind == Task.TASK else [],
        "open_sprints": project.sprints.filter(status__in=[Sprint.PLANNED, Sprint.ACTIVE]),
        "is_po": role == PO,
        "can_create": role in SM_UP,
        "can_assign_sprint": role in SM_UP,
        "can_edit": role in SM_UP or can_edit_task(request.user, task),
        "nav": "stories" if task.kind == Task.STORY else "backlog",
    }
    return render(request, "backlog/task_detail.html", ctx, status=status)


@project_role_required(ANY_ROLE, from_task_id)
def task_detail(request, task_id):
    return _detail_page(request, request.obj)


@require_POST
@project_role_required(STORY_CREATORS, from_task_id)
def activity_new(request, task_id):
    story = request.obj
    if story.kind != Task.STORY:
        raise Unprocessable("Las actividades se crean dentro de una historia.")
    form = ActivityForm(request.project, request.POST)
    if form.is_valid():
        try:
            services.create_task(request.project, kind=Task.TASK, parent=story, **form.cleaned_data)
            return redirect("task_detail", task_id=story.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _detail_page(request, story, activity_form=form, status=422)


@require_POST
@project_role_required(SM_UP, from_task_id)
def story_assign_sprint(request, task_id):
    form = AssignSprintForm(request.POST)
    if not form.is_valid():
        raise Unprocessable("Sprint no válido.")
    sprint = get_object_or_404(Sprint, pk=form.cleaned_data["sprint_id"], project=request.project)
    moved = services.assign_story_to_sprint(request.obj, sprint)
    messages.success(request, f"{len(moved)} actividad(es) asignada(s) a {sprint.name}.")
    return redirect_back(request, f"/tasks/{request.obj.pk}/")


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def comment_add(request, task_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        services.add_comment(request.obj, request.user, form.cleaned_data["body"])
        return redirect(f"/tasks/{request.obj.pk}/#comentarios")
    return _detail_page(request, request.obj, comment_form=form, status=422)


@require_POST
@project_role_required(ANY_ROLE, from_comment_id)
def comment_delete(request, comment_id):
    task = request.obj.task
    services.delete_comment(request.obj, request.user)
    return redirect(f"/tasks/{task.pk}/#comentarios")
