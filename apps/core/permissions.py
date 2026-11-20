from functools import wraps

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect

from .htmx import htmx_unauthorized, is_htmx

PO = "product_owner"
PM = "project_manager"
SM = "scrum_master"
DEV = "developer"

ANY_ROLE = (PO, PM, SM, DEV)
# Product Owner, Project Manager y Scrum Master gestionan el proyecto: sprints, columnas, presupuesto,
# asignaciones y también crean historias y actividades.
SM_UP = (PO, PM, SM)
STORY_CREATORS = SM_UP
PO_ONLY = (PO,)


def _get(app, model, **kw):
    try:
        return apps.get_model(app, model).objects.select_related("project").get(**kw)
    except apps.get_model(app, model).DoesNotExist:
        raise Http404 from None


def from_project_id(kwargs):
    Project = apps.get_model("projects", "Project")
    try:
        project = Project.objects.get(pk=kwargs["project_id"])
    except Project.DoesNotExist:
        raise Http404 from None
    return project, project


def from_task_id(kwargs):
    task = _get("backlog", "Task", pk=kwargs["task_id"])
    return task.project, task


def from_sprint_id(kwargs):
    sprint = _get("sprints", "Sprint", pk=kwargs["sprint_id"])
    return sprint.project, sprint


def from_column_id(kwargs):
    column = _get("board", "BoardColumn", pk=kwargs["column_id"])
    return column.project, column


def from_story_id(kwargs):
    story = _get("backlog", "Story", pk=kwargs["story_id"])
    return story.project, story


def from_comment_id(kwargs):
    Comment = apps.get_model("backlog", "Comment")
    comment = (
        Comment.objects.select_related("story__project", "task__project", "author").filter(pk=kwargs["comment_id"]).first()
    )
    if comment is None:
        raise Http404
    return comment.project, comment


def from_epic_id(kwargs):
    epic = _get("backlog", "Epic", pk=kwargs["epic_id"])
    return epic.project, epic


def from_criterion_id(kwargs):
    Criterion = apps.get_model("backlog", "AcceptanceCriterion")
    criterion = Criterion.objects.select_related("story__project").filter(pk=kwargs["criterion_id"]).first()
    if criterion is None:
        raise Http404
    return criterion.story.project, criterion


def from_department_id(kwargs):
    department = _get("budget", "Department", pk=kwargs["department_id"])
    return department.project, department


def project_role_required(roles, resolver=from_project_id):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if is_htmx(request):
                    return htmx_unauthorized(request)
                return redirect(f"/accounts/login/?next={request.path}")
            project, obj = resolver(kwargs)
            ProjectMember = apps.get_model("projects", "ProjectMember")
            member = ProjectMember.objects.filter(project=project, user=request.user).first()
            if member is None:
                raise Http404
            if member.role not in roles:
                raise PermissionDenied
            request.project, request.member, request.obj = project, member, obj
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def role_of(user, project_id):
    ProjectMember = apps.get_model("projects", "ProjectMember")
    member = ProjectMember.objects.filter(project_id=project_id, user=user).first()
    return member.role if member else None


def can_edit_task(user, task):
    role = role_of(user, task.project_id)
    if role == PO:
        return True
    return role == DEV and task.assignee_id == user.pk


def can_move_task(user, task):
    role = role_of(user, task.project_id)
    if role in SM_UP:
        return True
    return role == DEV and task.assignee_id in (None, user.pk)
