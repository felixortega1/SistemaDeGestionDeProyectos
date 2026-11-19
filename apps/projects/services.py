from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.board.services import create_default_board
from apps.core.exceptions import Conflict, NotFound, Unprocessable

from .models import Company, Project, ProjectMember

ROLES = {r for r, _ in ProjectMember.ROLES}


def parse_objectives(text):
    """Devuelve la lista de objetivos (uno por línea). Valida un máximo de 3."""
    items = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(items) > 3:
        raise Unprocessable("Un proyecto tiene como máximo 3 objetivos principales.")
    if any(len(i) > 200 for i in items):
        raise Unprocessable("Cada objetivo debe tener 200 caracteres o menos.")
    return items


def _check_project_dates(start_date, end_date):
    if start_date and end_date and end_date < start_date:
        raise Unprocessable("La fecha de fin no puede ser anterior a la de inicio.")


def companies_for(user):
    """Empresas donde el usuario participa en al menos un proyecto."""
    return Company.objects.filter(projects__members__user=user).distinct().order_by("name", "id")


def projects_for(user, company=None):
    qs = Project.objects.filter(members__user=user).select_related("company")
    if company is not None:
        qs = qs.filter(company=company)
    return qs.order_by("name")


def resolve_company(user, company=None, company_name=""):
    """Usa una empresa donde el usuario ya participa o crea una nueva con ese nombre."""
    if company is not None:
        if not companies_for(user).filter(pk=company.pk).exists():
            raise Unprocessable("No participas en esa empresa.")
        return company
    name = (company_name or "").strip()
    if not name:
        return Company.objects.get_or_create(name="General")[0]
    return Company.objects.create(name=name)


@transaction.atomic
def create_project(
    user, name, description="", *, company=None, company_name="", start_date=None, end_date=None, objectives=""
):
    _check_project_dates(start_date, end_date)
    items = parse_objectives(objectives)
    project = Project.objects.create(
        company=resolve_company(user, company, company_name),
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        objectives="\n".join(items),
        created_by=user,
    )
    ProjectMember.objects.create(project=project, user=user, role=ProjectMember.PRODUCT_OWNER)
    create_default_board(project)
    return project


@transaction.atomic
def update_project(
    project, user, name, description="", *, company=None, company_name="", start_date=None, end_date=None, objectives=""
):
    _check_project_dates(start_date, end_date)
    items = parse_objectives(objectives)
    if company is not None or (company_name or "").strip():
        project.company = resolve_company(user, company, company_name)
    project.name, project.description = name, description
    project.start_date, project.end_date = start_date, end_date
    project.objectives = "\n".join(items)
    project.save()
    return project


def add_member(project, email, role):
    if role not in ROLES or role == ProjectMember.PRODUCT_OWNER:
        raise Unprocessable("Rol no válido. El Product Owner solo se asigna con una transferencia.")
    User = get_user_model()
    try:
        user = User.objects.get(email=email.strip().lower())
    except User.DoesNotExist:
        raise Unprocessable("No hay ningún usuario registrado con ese correo.") from None
    if ProjectMember.objects.filter(project=project, user=user).exists():
        raise Unprocessable("Esa persona ya es miembro del proyecto.")
    return ProjectMember.objects.create(project=project, user=user, role=role)


def _member(project, user_id):
    try:
        return ProjectMember.objects.get(project=project, user_id=user_id)
    except ProjectMember.DoesNotExist:
        raise NotFound("Miembro no encontrado.") from None


@transaction.atomic
def change_role(project, user_id, role):
    if role == ProjectMember.PRODUCT_OWNER:
        raise Unprocessable("Solo una transferencia crea un Product Owner.")
    if role not in ROLES:
        raise Unprocessable("Rol no válido.")
    member = _member(project, user_id)
    if member.role == ProjectMember.PRODUCT_OWNER:
        raise Conflict("Para cambiar el rol del Product Owner, transfiere el rol primero.")
    member.role = role
    member.save(update_fields=["role"])
    return member


@transaction.atomic
def remove_member(project, user_id):
    member = _member(project, user_id)
    if member.role == ProjectMember.PRODUCT_OWNER:
        raise Conflict("No se puede quitar al Product Owner.")
    try:
        Task = apps.get_model("backlog", "Task")
    except LookupError:
        Task = None
    if Task is not None:
        pending = Task.objects.filter(project=project, assignee_id=user_id).exclude(column__is_done=True)
        if pending.exists():
            raise Conflict("El miembro tiene tareas asignadas sin terminar.")
    member.delete()


@transaction.atomic
def transfer_product_owner(project, new_po_user_id, outgoing_role):
    if outgoing_role not in (ProjectMember.PROJECT_MANAGER, ProjectMember.SCRUM_MASTER, ProjectMember.DEVELOPER):
        raise Unprocessable("El Product Owner saliente debe pasar a project_manager, scrum_master o developer.")
    current = ProjectMember.objects.select_for_update().get(project=project, role=ProjectMember.PRODUCT_OWNER)
    target = _member(project, new_po_user_id)
    if target.pk == current.pk:
        raise Unprocessable("Esa persona ya es el Product Owner.")
    current.role = outgoing_role
    current.save(update_fields=["role"])
    target.role = ProjectMember.PRODUCT_OWNER
    target.save(update_fields=["role"])
