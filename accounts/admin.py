from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User


class UserCreationForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserEditForm
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Persönliche Daten", {"fields": ("first_name", "last_name", "phone")}),
        ("Berechtigungen", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Wichtige Daten", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
