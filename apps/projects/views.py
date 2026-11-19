from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.exceptions import Unprocessable
from apps.core.permissions import ANY_ROLE, PO_ONLY, project_role_required

from . import services
from .forms import AddMemberForm, ProjectForm, RoleForm, TransferForm
from .models import ProjectMember


def _summarize(user, projects):
    """Agrega a cada proyecto su rol, el sprint activo y el avance de sus tareas (solo lectura)."""
    Task = apps.get_model("backlog", "Task")
    Sprint = apps.get_model("sprints", "Sprint")
    roles = dict(ProjectMember.ROLES)
    my_roles = dict(ProjectMember.objects.filter(user=user).values_list("project_id", "role"))
    active = {s.project_id: s for s in Sprint.objects.filter(project__in=projects, status="active")}
    for p in projects:
        p.role_label = roles.get(my_roles.get(p.pk), "")
        p.active_sprint = active.get(p.pk)
        p.done = p.total = p.percent = 0
        if p.active_sprint:
            tasks = Task.objects.filter(sprint=p.active_sprint)
            p.total = tasks.count()
            p.done = tasks.filter(column__is_done=True).count()
            p.percent = round(100 * p.done / p.total) if p.total else 0
    return projects


@login_required
def company_list(request):
    """Pantalla de inicio: las empresas donde el usuario tiene proyectos."""
    companies = list(services.companies_for(request.user))
    counts = {}
    for p in services.projects_for(request.user):
        counts[p.company_id] = counts.get(p.company_id, 0) + 1
    for c in companies:
        c.my_projects = counts.get(c.pk, 0)
    return render(request, "projects/companies.html", {"companies": companies})


@login_required
def company_detail(request, company_id):
    company = get_object_or_404(services.companies_for(request.user), pk=company_id)
    projects = _summarize(request.user, list(services.projects_for(request.user, company)))
    return render(request, "projects/company.html", {"company": company, "projects": projects})


@login_required
def project_list(request):
    """Todos mis proyectos, de todas las empresas."""
    projects = _summarize(request.user, list(services.projects_for(request.user)))
    return render(request, "projects/list.html", {"projects": projects})


@login_required
def project_new(request):
    initial = {}
    if request.GET.get("company"):
        initial["company"] = request.GET["company"]
    if request.method == "POST":
        form = ProjectForm(request.user, request.POST)
        if form.is_valid():
            try:
                project = services.create_project(request.user, **form.cleaned_data)
                messages.success(request, "Proyecto creado.")
                return redirect("project_detail", project_id=project.pk)
            except Unprocessable as e:
                form.add_error(None, e.message)
        return render(request, "projects/new.html", {"form": form, "title": "Nuevo proyecto"}, status=422)
    return render(request, "projects/new.html", {"form": ProjectForm(request.user, initial=initial), "title": "Nuevo proyecto"})


@project_role_required(PO_ONLY)
def project_edit(request, project_id):
    project = request.project
    if request.method == "POST":
        form = ProjectForm(request.user, request.POST)
        if form.is_valid():
            try:
                services.update_project(project, request.user, **form.cleaned_data)
                messages.success(request, "Proyecto actualizado.")
                return redirect("project_detail", project_id=project.pk)
            except Unprocessable as e:
                form.add_error(None, e.message)
        return render(request, "projects/new.html", {"form": form, "project": project, "title": "Editar proyecto"}, status=422)
    initial = {
        "company": project.company_id, "name": project.name, "description": project.description,
        "start_date": project.start_date, "end_date": project.end_date, "objectives": project.objectives,
    }
    return render(
        request, "projects/new.html",
        {"form": ProjectForm(request.user, initial=initial), "project": project, "title": "Editar proyecto"},
    )


@project_role_required(ANY_ROLE)
def project_detail(request, project_id):
    return redirect("stories", project_id=project_id)


def _members_page(request, add_form=None, status=200):
    project = request.project
    ctx = {
        "project": project,
        "members": project.members.select_related("user").order_by("user__email"),
        "add_form": add_form or AddMemberForm(),
        "roles": ProjectMember.ROLES,
        "is_po": request.member.role == ProjectMember.PRODUCT_OWNER,
        "nav": "members",
    }
    return render(request, "projects/members.html", ctx, status=status)


@project_role_required(ANY_ROLE)
def members(request, project_id):
    return _members_page(request)


@require_POST
@project_role_required(PO_ONLY)
def member_add(request, project_id):
    form = AddMemberForm(request.POST)
    if form.is_valid():
        try:
            services.add_member(request.project, **form.cleaned_data)
            return redirect("members", project_id=project_id)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _members_page(request, form, 422)


@require_POST
@project_role_required(PO_ONLY)
def member_role(request, project_id, user_id):
    form = RoleForm(request.POST)
    if not form.is_valid():
        raise Unprocessable("Rol no válido.")
    services.change_role(request.project, user_id, form.cleaned_data["role"])
    return redirect("members", project_id=project_id)


@require_POST
@project_role_required(PO_ONLY)
def member_remove(request, project_id, user_id):
    services.remove_member(request.project, user_id)
    return redirect("members", project_id=project_id)


@require_POST
@project_role_required(PO_ONLY)
def transfer_po(request, project_id):
    form = TransferForm(request.POST)
    if not form.is_valid():
        raise Unprocessable("Datos de transferencia no válidos.")
    services.transfer_product_owner(request.project, form.cleaned_data["user_id"], form.cleaned_data["outgoing_role"])
    messages.success(request, "Product Owner transferido.")
    return redirect("company_detail", company_id=request.project.company_id)
