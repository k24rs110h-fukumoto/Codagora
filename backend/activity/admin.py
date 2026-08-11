from django.contrib import admin

from .models import ActivityEvent


@admin.register(ActivityEvent)
class ActivityEventAdmin(
    admin.ModelAdmin
):
    list_display = (
        "event_type",
        "category",
        "workspace",
        "actor",
        "visibility",
        "occurred_at",
    )

    list_filter = (
        "category",
        "visibility",
        "source",
        "event_type",
    )

    search_fields = (
        "title",
        "summary",
        "object_id",
        "workspace__name",
        "workspace__slug",
        "actor__email",
    )

    readonly_fields = (
        "id",
        "workspace",
        "actor",
        "subject_user",
        "category",
        "event_type",
        "visibility",
        "source",
        "object_type",
        "object_id",
        "title",
        "summary",
        "metadata",
        "deduplication_key",
        "occurred_at",
        "created_at",
    )

    ordering = (
        "-occurred_at",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False