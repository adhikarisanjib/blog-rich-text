from django.contrib import admin

from .models import Token, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "date_joined", "is_email_verified", "is_staff", "is_superuser")
    readonly_fields = ("id", "date_joined", "last_login", "is_superuser", "is_staff", "password")
    search_fields = ("email", "name")
    list_filter = ()
    filter_horizontal = ()
    fieldsets = ()
    ordering = ("email",)


class TokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at")
    readonly_fields = ("id", "created_at")
    search_fields = ("user",)

admin.site.register(Token, TokenAdmin)
