from django.contrib import admin

from .models import (
    Channel,
    Message,
)


@admin.register(Channel)
class ChannelAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "name",
        "workspace",
        "channel_type",
        "position",
        "is_archived",
        "created_by",
        "created_at",
    )

    list_filter = (
        "channel_type",
        "is_archived",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "workspace__name",
        "workspace__slug",
        "created_by__email",
        "created_by__display_name",
    )

    autocomplete_fields = (
        "workspace",
        "created_by",
        "archived_by",
    )

    readonly_fields = (
        "id",
        "archived_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "workspace",
        "position",
    )


@admin.register(Message)
class MessageAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "id",
        "channel",
        "author",
        "is_edited",
        "deleted_at",
        "created_at",
    )

    list_filter = (
        "is_edited",
        "deleted_at",
        "created_at",
    )

    search_fields = (
        "content",
        "author__email",
        "author__display_name",
        "channel__name",
        "channel__workspace__name",
    )

    autocomplete_fields = (
        "channel",
        "author",
        "reply_to",
        "deleted_by",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
        "deleted_by",
    )

    ordering = (
        "-created_at",
    )