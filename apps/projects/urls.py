from django.urls import path

from . import views

urlpatterns = [
    path("", views.company_list, name="company_list"),
    path("companies/<int:company_id>/", views.company_detail, name="company_detail"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/new/", views.project_new, name="project_new"),
    path("projects/<int:project_id>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path("projects/<int:project_id>/members/", views.members, name="members"),
    path("projects/<int:project_id>/members/add/", views.member_add, name="member_add"),
    path("projects/<int:project_id>/members/<int:user_id>/role/", views.member_role, name="member_role"),
    path("projects/<int:project_id>/members/<int:user_id>/remove/", views.member_remove, name="member_remove"),
    path("projects/<int:project_id>/transfer-po/", views.transfer_po, name="transfer_po"),
]
