from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.exceptions import Unprocessable
from apps.core.htmx import fragment_or_redirect, is_htmx, redirect_back
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
    from_criterion_id,
    from_epic_id,
    from_story_id,
    from_task_id,
    project_role_required,
)
from apps.sprints.models import Sprint

from . import services
from .forms import (
    ASSIGNEE_ONLY,
    FULL,
    NO_ASSIGNEE,
    AssignSprintForm,
    BacklogFilterForm,
    CommentForm,
    CriterionForm,
    DependencyForm,
    EpicForm,
    MilestoneForm,
    StoryForm,
    StoryTaskForm,
    TaskForm,
)
from .models import Story, Task

PRIORITY_RANK = {Story.HIGH: 0, Story.MEDIUM: 1, Story.LOW: 2}


# ---------------------------------------------------------------- filtros del backlog
def _filters(request):
    """Lee `priority` y `epic` de la URL. `epic` es un id o `none`; un valor inválido se ignora."""
    form = BacklogFilterForm(request.GET)
    data = form.cleaned_data if form.is_valid() else {}
    priority = data.get("priority", "")
    epic = (data.get("epic") or "").strip()
    if epic != "none" and not epic.isdigit():
        epic = ""
    return priority, epic


def _story_matches(story, priority, epic):
    if priority and story.priority != priority:
        return False
    if epic == "none":
        return story.epic_id is None
    if epic:
        return story.epic_id == int(epic)
    return True


def _task_matches(task, priority, epic):
    """Una tarea hereda la prioridad y la épica de su historia; una tarea suelta no tiene ninguna."""
    if task.story_id is None:
        return not priority and epic in ("", "none")
    return _story_matches(task.story, priority, epic)


def _task_rank(task):
    return PRIORITY_RANK.get(task.story.priority, 1) if task.story_id else PRIORITY_RANK[Story.MEDIUM]


# ---------------------------------------------------------------- backlog y tareas
def _backlog_page(request, status=200, task_form=None, milestone_form=None):
    project = request.project
    priority, epic = _filters(request)
    tasks = list(Task.objects.filter(project=project).select_related("sprint", "assignee", "story").order_by("id"))
    tasks.sort(key=_task_rank)  # estable: dentro de la misma prioridad queda el orden por id
    by_story = {}
    for t in tasks:
        if t.story_id:
            by_story.setdefault(t.story_id, []).append(t)
    ordered = services.order_by_priority(Story.objects.filter(project=project).select_related("epic"))
    stories = [s for s in ordered if _story_matches(s, priority, epic)]
    for s in stories:
        s.child_list = by_story.get(s.pk, [])
    shown = [t for t in tasks if _task_matches(t, priority, epic)]
    ctx = {
        "project": project,
        "stories": stories,
        "backlog_tasks": [t for t in shown if t.sprint_id is None],
        "sprint_tasks": [t for t in shown if t.sprint_id is not None],
        "milestones": project.milestones.all(),
        "open_sprints": project.sprints.filter(status__in=[Sprint.PLANNED, Sprint.ACTIVE]),
        "task_form": task_form or TaskForm(project),
        "milestone_form": milestone_form or MilestoneForm(),
        "epics": project.epics.all(),
        "priorities": Story.PRIORITIES,
        "filter_priority": priority,
        "filter_epic": epic,
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


def _task_form_page(request, task, form, dep_form=None, status=200, mode=FULL):
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
    initial = {f: getattr(task, f) for f in services.TASK_FIELDS}
    if request.method == "POST":
        form = TaskForm(request.project, request.POST, mode=mode, task=task)
        if form.is_valid():
            try:
                services.update_task(task, **form.cleaned_data)
                return redirect("backlog", project_id=request.project.pk)
            except Unprocessable as e:
                form.add_error(None, e.message)
        return _task_form_page(request, task, form, status=422, mode=mode)
    form = TaskForm(request.project, initial=initial, mode=mode, task=task)
    return _task_form_page(request, task, form, mode=mode)


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
@project_role_required(SM_UP, from_task_id)
def task_unassign_sprint(request, task_id):
    services.unassign_sprint(request.obj)
    messages.success(request, "Tarea devuelta al backlog.")
    return redirect_back(request, f"/projects/{request.project.pk}/sprints/")


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
    mode = _edit_mode(request, task)
    edit_form = TaskForm(
        request.project, initial={f: getattr(task, f) for f in services.TASK_FIELDS}, mode=mode, task=task
    )
    return _task_form_page(request, task, edit_form, dep_form=form, status=422, mode=mode)


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def dependency_delete(request, task_id, dep_id):
    if not can_edit_task(request.user, request.obj):
        raise PermissionDenied
    services.remove_dependency(request.obj, dep_id)
    return redirect("task_edit", task_id=request.obj.pk)


def _task_detail_page(request, task, comment_form=None, status=200):
    role = request.member.role
    ctx = {
        "project": request.project,
        "task": task,
        "comments": task.comments.select_related("author"),
        "comment_form": comment_form or CommentForm(),
        "dependencies": task.dependencies.select_related("depends_on"),
        "open_sprints": request.project.sprints.filter(status__in=[Sprint.PLANNED, Sprint.ACTIVE]),
        "is_po": role == PO,
        "can_assign_sprint": role in SM_UP,
        "can_edit": role in SM_UP or can_edit_task(request.user, task),
        "nav": "backlog",
    }
    return render(request, "backlog/task_detail.html", ctx, status=status)


@project_role_required(ANY_ROLE, from_task_id)
def task_detail(request, task_id):
    return _task_detail_page(request, request.obj)


@require_POST
@project_role_required(ANY_ROLE, from_task_id)
def comment_add(request, task_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        services.add_comment(request.obj, request.user, form.cleaned_data["body"])
        return redirect(f"/tasks/{request.obj.pk}/#comentarios")
    return _task_detail_page(request, request.obj, comment_form=form, status=422)


@require_POST
@project_role_required(ANY_ROLE, from_comment_id)
def comment_delete(request, comment_id):
    comment = request.obj
    target = comment.target
    services.delete_comment(comment, request.user)
    base = "stories" if isinstance(target, Story) else "tasks"
    return redirect(f"/{base}/{target.pk}/#comentarios")


# ---------------------------------------------------------------- historias
def _story_rows(project):
    tasks = list(Task.objects.filter(project=project, story__isnull=False).select_related("column", "sprint"))
    stories = list(services.order_by_priority(Story.objects.filter(project=project).select_related("epic")))
    counts = services.criteria_counts(project)
    for st in stories:
        mine = [t for t in tasks if t.story_id == st.pk]
        st.total = len(mine)
        st.done = sum(1 for t in mine if t.column_id and t.column.is_done)
        st.percent = round(100 * st.done / st.total) if st.total else 0
        st.unassigned = sum(1 for t in mine if t.sprint_id is None)
        st.crit_done, st.crit_total = counts.get(st.pk, (0, 0))
    return stories, Task.objects.filter(project=project, story__isnull=True).count()


def _group(epic, stories):
    total = sum(s.total for s in stories)
    done = sum(s.done for s in stories)
    return {
        "epic": epic,
        "stories": stories,
        "total": total,
        "done": done,
        "percent": round(100 * done / total) if total else 0,
    }


def _epic_groups(project, stories, epic_filter):
    """Agrupa las historias por épica y deja «Sin épica» al final. `epic_filter` es un id, `none` o vacío."""
    groups = []
    for epic in project.epics.all():
        if epic_filter and epic_filter != str(epic.pk):
            continue
        mine = [s for s in stories if s.epic_id == epic.pk]
        groups.append(_group(epic, mine))
    if epic_filter in ("", "none"):
        groups.append(_group(None, [s for s in stories if s.epic_id is None]))
    return groups


def _product_owner(project):
    member = project.members.filter(role=PO).select_related("user").first()
    return member.user if member else None


def _stories_page(request, form=None, status=200, epic_form=None):
    _, epic_filter = _filters(request)
    stories, loose = _story_rows(request.project)
    groups = _epic_groups(request.project, stories, epic_filter)
    ctx = {
        "project": request.project,
        "stories": [s for g in groups for s in g["stories"]],
        "groups": groups,
        "epics": request.project.epics.all(),
        "filter_epic": epic_filter,
        "loose_count": loose,
        "story_form": form or StoryForm(project=request.project),
        "epic_form": epic_form or EpicForm(),
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
    form = StoryForm(request.POST, project=request.project)
    if form.is_valid():
        try:
            story = services.create_story(request.project, **form.cleaned_data)
            return redirect("story_detail", story_id=story.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _stories_page(request, form, 422)


def _criteria_context(request, story, error=None):
    criteria = list(story.criteria.all())
    done = sum(1 for c in criteria if c.is_done)
    return {
        "story": story,
        "criteria": criteria,
        "criteria_done": done,
        "criteria_total": len(criteria),
        "criteria_percent": round(100 * done / len(criteria)) if criteria else 0,
        "criterion_form": CriterionForm(),
        "can_manage_criteria": request.member.role in SM_UP,
        "criteria_error": error,
    }


def _story_page(request, story, comment_form=None, task_form=None, status=200):
    project = request.project
    role = request.member.role
    tasks = list(story.tasks.select_related("column", "sprint", "assignee").order_by("id"))
    ctx = {
        "project": project,
        "story": story,
        "tasks": tasks,
        "comments": story.comments.select_related("author"),
        "comment_form": comment_form or CommentForm(),
        "task_form": task_form or StoryTaskForm(project),
        "open_sprints": project.sprints.filter(status__in=[Sprint.PLANNED, Sprint.ACTIVE]),
        "is_po": role == PO,
        "can_create": role in SM_UP,
        "can_assign_sprint": role in SM_UP,
        "can_edit": role in SM_UP,
        "nav": "stories",
    }
    ctx.update(_criteria_context(request, story))
    return render(request, "backlog/story_detail.html", ctx, status=status)


@project_role_required(ANY_ROLE, from_story_id)
def story_detail(request, story_id):
    return _story_page(request, request.obj)


@project_role_required(SM_UP, from_story_id)
def story_edit(request, story_id):
    story = request.obj
    if request.method == "POST":
        form = StoryForm(request.POST, project=request.project)
        if form.is_valid():
            try:
                services.update_story(story, **form.cleaned_data)
                return redirect("story_detail", story_id=story.pk)
            except Unprocessable as e:
                form.add_error(None, e.message)
        status = 422
    else:
        initial = {f: getattr(story, f) for f in services.STORY_FIELDS}
        form = StoryForm(initial=initial, project=request.project)
        status = 200
    ctx = {"project": request.project, "story": story, "form": form, "nav": "stories"}
    return render(request, "backlog/story_form.html", ctx, status=status)


@require_POST
@project_role_required(PO_ONLY, from_story_id)
def story_delete(request, story_id):
    services.delete_story(request.obj)
    return redirect("stories", project_id=request.project.pk)


@require_POST
@project_role_required(STORY_CREATORS, from_story_id)
def story_task_new(request, story_id):
    story = request.obj
    form = StoryTaskForm(request.project, request.POST)
    if form.is_valid():
        try:
            services.create_task(request.project, story=story, **form.cleaned_data)
            return redirect("story_detail", story_id=story.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _story_page(request, story, task_form=form, status=422)


@require_POST
@project_role_required(SM_UP, from_story_id)
def story_assign_sprint(request, story_id):
    form = AssignSprintForm(request.POST)
    if not form.is_valid():
        raise Unprocessable("Sprint no válido.")
    sprint = get_object_or_404(Sprint, pk=form.cleaned_data["sprint_id"], project=request.project)
    moved = services.assign_story_to_sprint(request.obj, sprint)
    messages.success(request, f"{len(moved)} tarea(s) asignada(s) a {sprint.name}.")
    return redirect_back(request, f"/stories/{request.obj.pk}/")


@require_POST
@project_role_required(ANY_ROLE, from_story_id)
def story_comment_add(request, story_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        services.add_comment(request.obj, request.user, form.cleaned_data["body"])
        return redirect(f"/stories/{request.obj.pk}/#comentarios")
    return _story_page(request, request.obj, comment_form=form, status=422)


# ---------------------------------------------------------------- épicas
@require_POST
@project_role_required(SM_UP)
def epic_new(request, project_id):
    form = EpicForm(request.POST)
    if form.is_valid():
        try:
            services.create_epic(request.project, **form.cleaned_data)
            return redirect("stories", project_id=project_id)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _stories_page(request, status=422, epic_form=form)


@require_POST
@project_role_required(SM_UP, from_epic_id)
def epic_edit(request, epic_id):
    form = EpicForm(request.POST)
    if form.is_valid():
        try:
            services.update_epic(request.obj, **form.cleaned_data)
            return redirect("stories", project_id=request.project.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    messages.error(request, "; ".join(m for errs in form.errors.values() for m in errs))
    return _stories_page(request, status=422)


@require_POST
@project_role_required(PO_ONLY, from_epic_id)
def epic_delete(request, epic_id):
    services.delete_epic(request.obj)
    return redirect("stories", project_id=request.project.pk)


# ---------------------------------------------------------------- criterios de aceptación
def _criteria_response(request, story, error=None):
    """Fragmento HTMX (siempre 200, para que HTMX lo intercambie y muestre el error dentro) o redirección."""
    if error and not is_htmx(request):
        messages.error(request, error)
    return fragment_or_redirect(
        request, "backlog/_criteria.html", _criteria_context(request, story, error), f"/stories/{story.pk}/#criterios"
    )


@require_POST
@project_role_required(SM_UP, from_story_id)
def criterion_add(request, story_id):
    story = request.obj
    form = CriterionForm(request.POST)
    if not form.is_valid():
        return _criteria_response(request, story, "Escribe el criterio (máximo 500 caracteres).")
    try:
        services.add_criterion(story, form.cleaned_data["text"])
    except Unprocessable as e:
        return _criteria_response(request, story, e.message)
    return _criteria_response(request, story)


@require_POST
@project_role_required(ANY_ROLE, from_criterion_id)
def criterion_toggle(request, criterion_id):
    services.toggle_criterion(request.obj, request.user)
    return _criteria_response(request, request.obj.story)


@require_POST
@project_role_required(SM_UP, from_criterion_id)
def criterion_delete(request, criterion_id):
    story = request.obj.story
    services.delete_criterion(request.obj)
    return _criteria_response(request, story)
