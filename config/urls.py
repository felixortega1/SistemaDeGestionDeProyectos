from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.projects.urls")),
    path("", include("apps.sprints.urls")),
    path("", include("apps.backlog.urls")),
    path("", include("apps.board.urls")),
    path("", include("apps.gantt.urls")),
    path("", include("apps.budget.urls")),
    path("", include("apps.tickets.urls")),
]
