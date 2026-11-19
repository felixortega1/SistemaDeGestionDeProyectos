from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_id>/sprints/", views.sprints, name="sprints"),
    path("projects/<int:project_id>/sprints/new/", views.sprint_new, name="sprint_new"),
    path("sprints/<int:sprint_id>/edit/", views.sprint_edit, name="sprint_edit"),
    path("sprints/<int:sprint_id>/start/", views.sprint_start, name="sprint_start"),
    path("sprints/<int:sprint_id>/close/", views.sprint_close, name="sprint_close"),
]
