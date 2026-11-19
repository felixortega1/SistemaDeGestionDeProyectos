from django.contrib import admin
from django.contrib.sessions.models import Session

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_active", "is_staff")
    search_fields = ("email", "name")
    exclude = ("password",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "expire_date")
    readonly_fields = ("session_key", "session_data", "expire_date")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
