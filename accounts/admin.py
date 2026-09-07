from django.contrib import admin
from .models import User,ContactMessage
from django.contrib.auth.admin import UserAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role Info", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Role Info", {"fields": ("role",)}),)
    


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "subject",
        "message",
        "phone",
        "created_at",
        "is_read",
    )

    list_filter = ("is_read", "created_at","email","phone")
    search_fields = ("name", "email", "subject", "message","phone")
    readonly_fields = ("created_at",)

    list_editable = ("is_read",)