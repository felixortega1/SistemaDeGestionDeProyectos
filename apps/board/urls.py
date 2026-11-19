from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_id>/board/", views.board, name="board"),
    path("tasks/<int:task_id>/move/", views.task_move, name="task_move"),
    path("tasks/<int:task_id>/board-comment/", views.board_comment, name="board_comment"),
    path("projects/<int:project_id>/columns/", views.columns, name="columns"),
    path("projects/<int:project_id>/columns/new/", views.column_new, name="column_new"),
    path("projects/<int:project_id>/columns/transitions/", views.transitions, name="transitions"),
    path("columns/<int:column_id>/edit/", views.column_edit, name="column_edit"),
]
