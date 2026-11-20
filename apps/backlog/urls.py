from django.urls import path

from . import views

urlpatterns = [
    # historias
    path("projects/<int:project_id>/stories/", views.stories, name="stories"),
    path("projects/<int:project_id>/stories/new/", views.story_new, name="story_new"),
    path("stories/<int:story_id>/", views.story_detail, name="story_detail"),
    path("stories/<int:story_id>/edit/", views.story_edit, name="story_edit"),
    path("stories/<int:story_id>/delete/", views.story_delete, name="story_delete"),
    path("stories/<int:story_id>/tasks/new/", views.story_task_new, name="story_task_new"),
    path("stories/<int:story_id>/assign-sprint/", views.story_assign_sprint, name="story_assign_sprint"),
    path("stories/<int:story_id>/comments/add/", views.story_comment_add, name="story_comment_add"),
    path("stories/<int:story_id>/criteria/add/", views.criterion_add, name="criterion_add"),
    path("criteria/<int:criterion_id>/toggle/", views.criterion_toggle, name="criterion_toggle"),
    path("criteria/<int:criterion_id>/delete/", views.criterion_delete, name="criterion_delete"),
    # épicas
    path("projects/<int:project_id>/epics/new/", views.epic_new, name="epic_new"),
    path("epics/<int:epic_id>/edit/", views.epic_edit, name="epic_edit"),
    path("epics/<int:epic_id>/delete/", views.epic_delete, name="epic_delete"),
    # backlog y tareas
    path("projects/<int:project_id>/backlog/", views.backlog, name="backlog"),
    path("projects/<int:project_id>/tasks/new/", views.task_new, name="task_new"),
    path("projects/<int:project_id>/milestones/new/", views.milestone_new, name="milestone_new"),
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),
    path("tasks/<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("tasks/<int:task_id>/assign-sprint/", views.task_assign_sprint, name="task_assign_sprint"),
    path("tasks/<int:task_id>/unassign-sprint/", views.task_unassign_sprint, name="task_unassign_sprint"),
    path("tasks/<int:task_id>/dependencies/add/", views.dependency_add, name="dependency_add"),
    path("tasks/<int:task_id>/dependencies/<int:dep_id>/delete/", views.dependency_delete, name="dependency_delete"),
    path("tasks/<int:task_id>/comments/add/", views.comment_add, name="comment_add"),
    path("comments/<int:comment_id>/delete/", views.comment_delete, name="comment_delete"),
]
