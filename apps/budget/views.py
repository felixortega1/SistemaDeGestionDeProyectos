from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.exceptions import Unprocessable
from apps.core.permissions import ANY_ROLE, SM_UP, from_department_id, project_role_required

from . import services
from .forms import DepartmentForm


def _page(request, new_form=None, status=200):
    departments = list(request.project.departments.select_related("updated_by"))
    can_edit = request.member.role in SM_UP
    for d in departments:
        d.form = DepartmentForm(initial={"name": d.name, "budget_amount": d.budget_amount, "currency": d.currency})
    ctx = {
        "project": request.project,
        "departments": departments,
        "new_form": new_form or DepartmentForm(),
        "can_edit": can_edit,
        "nav": "budget",
    }
    return render(request, "budget/budget.html", ctx, status=status)


@project_role_required(ANY_ROLE)
def budget(request, project_id):
    return _page(request)


@require_POST
@project_role_required(SM_UP)
def department_new(request, project_id):
    form = DepartmentForm(request.POST)
    if form.is_valid():
        try:
            services.create_department(request.project, request.user, **form.cleaned_data)
            return redirect("budget", project_id=project_id)
        except Unprocessable as e:
            form.add_error(None, e.message)
    return _page(request, form, 422)


@require_POST
@project_role_required(SM_UP, from_department_id)
def department_edit(request, department_id):
    form = DepartmentForm(request.POST)
    if form.is_valid():
        try:
            services.update_department(request.obj, request.user, **form.cleaned_data)
            return redirect("budget", project_id=request.project.pk)
        except Unprocessable as e:
            form.add_error(None, e.message)
    messages.error(request, "; ".join(m for errs in form.errors.values() for m in errs))
    return _page(request, None, 422)


@require_POST
@project_role_required(SM_UP, from_department_id)
def department_delete(request, department_id):
    services.delete_department(request.obj)
    return redirect("budget", project_id=request.project.pk)
