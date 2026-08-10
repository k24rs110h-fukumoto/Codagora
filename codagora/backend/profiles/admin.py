from django.contrib import admin

from .models import DeveloperProfile


@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(
    admin.ModelAdmin
):
    list_display = (
        "user",
        "headline",
        "availability",
        "is_public",
        "updated_at",
    )

    list_filter = (
        "availability",
        "is_public",
        "show_projects",
        "show_activity",
    )

    search_fields = (
        "user__email",
        "user__display_name",
        "user__handle",
        "headline",
        "bio",
        "location_label",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-updated_at",
    )