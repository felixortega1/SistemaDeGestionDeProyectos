from django.shortcuts import render
from django.utils import timezone

from apps.core.permissions import ANY_ROLE, project_role_required

from .services import build_gantt


@project_role_required(ANY_ROLE)
def gantt(request, project_id):
    data = build_gantt(request.project, timezone.localdate())
    return render(request, "gantt/gantt.html", {"project": request.project, "data": data, "nav": "gantt"})
