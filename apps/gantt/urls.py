from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_id>/gantt/", views.gantt, name="gantt"),
]
