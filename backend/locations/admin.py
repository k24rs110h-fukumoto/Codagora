from django.contrib import admin

from .models import (
    WorkspaceLocationShare,
    WorkspacePlace,
)


@admin.register(WorkspacePlace)
class WorkspacePlaceAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "name",
        "workspace",
        "address",
        "created_by",
        "deleted_at",
        "created_at",
    )

    list_filter = (
        "deleted_at",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "address",
        "workspace__name",
        "workspace__slug",
        "created_by__email",
        "created_by__display_name",
    )

    autocomplete_fields = (
        "workspace",
        "created_by",
        "deleted_by",
    )

    readonly_fields = (
        "id",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )


@admin.register(
    WorkspaceLocationShare
)
class WorkspaceLocationShareAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "user",
        "workspace",
        "label",
        "started_at",
        "expires_at",
        "ended_at",
    )

    list_filter = (
        "started_at",
        "expires_at",
        "ended_at",
    )

    search_fields = (
        "user__email",
        "user__display_name",
        "user__handle",
        "workspace__name",
        "label",
        "note",
    )

    autocomplete_fields = (
        "workspace",
        "user",
        "place",
    )

    readonly_fields = (
        "id",
        "workspace",
        "user",
        "place",
        "label",
        "note",
        "latitude",
        "longitude",
        "accuracy_meters",
        "started_at",
        "expires_at",
        "ended_at",
        "updated_at",
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