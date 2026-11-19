from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_id>/budget/", views.budget, name="budget"),
    path("projects/<int:project_id>/departments/new/", views.department_new, name="department_new"),
    path("departments/<int:department_id>/edit/", views.department_edit, name="department_edit"),
    path("departments/<int:department_id>/delete/", views.department_delete, name="department_delete"),
]
