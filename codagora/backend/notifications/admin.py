from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(
    admin.ModelAdmin
):
    list_display = (
        "notification_type",
        "recipient",
        "actor",
        "workspace",
        "read_at",
        "created_at",
    )

    list_filter = (
        "category",
        "notification_type",
        "read_at",
        "created_at",
    )

    search_fields = (
        "title",
        "body",
        "recipient__email",
        "actor__email",
        "workspace__name",
        "workspace__slug",
        "object_id",
    )

    readonly_fields = (
        "id",
        "recipient",
        "actor",
        "workspace",
        "notification_type",
        "category",
        "title",
        "body",
        "object_type",
        "object_id",
        "metadata",
        "deduplication_key",
        "read_at",
        "created_at",
    )

    ordering = (
        "-created_at",
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