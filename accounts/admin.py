from django.contrib import admin

from .models import ANONYMOUS_EMAIL, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "email", "username", "is_staff", "registration_date", "last_login")
    list_filter = ("is_staff",)
    search_fields = ("email", "username")
    ordering = ("user_id",)
    fields = ("email", "username", "is_staff", "registration_date", "last_login")
    readonly_fields = ("registration_date", "last_login")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.email == ANONYMOUS_EMAIL:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.email == ANONYMOUS_EMAIL:
            return False
        return super().has_delete_permission(request, obj)