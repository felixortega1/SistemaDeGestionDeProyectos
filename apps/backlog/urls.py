from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_id>/stories/", views.stories, name="stories"),
    path("projects/<int:project_id>/stories/new/", views.story_new, name="story_new"),
    path("projects/<int:project_id>/backlog/", views.backlog, name="backlog"),
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),
    path("tasks/<int:task_id>/activities/new/", views.activity_new, name="activity_new"),
    path("tasks/<int:task_id>/assign-story/", views.story_assign_sprint, name="story_assign_sprint"),
    path("tasks/<int:task_id>/comments/add/", views.comment_add, name="comment_add"),
    path("comments/<int:comment_id>/delete/", views.comment_delete, name="comment_delete"),
    path("projects/<int:project_id>/tasks/new/", views.task_new, name="task_new"),
    path("tasks/<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("tasks/<int:task_id>/assign-sprint/", views.task_assign_sprint, name="task_assign_sprint"),
    path("tasks/<int:task_id>/dependencies/add/", views.dependency_add, name="dependency_add"),
    path("tasks/<int:task_id>/dependencies/<int:dep_id>/delete/", views.dependency_delete, name="dependency_delete"),
    path("projects/<int:project_id>/milestones/new/", views.milestone_new, name="milestone_new"),
]
