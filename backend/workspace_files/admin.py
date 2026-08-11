from django.contrib import admin

from .models import (
    WorkspaceFile,
    WorkspaceFolder,
)


@admin.register(WorkspaceFolder)
class WorkspaceFolderAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "name",
        "workspace",
        "parent",
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
        "workspace__name",
        "workspace__slug",
        "created_by__email",
        "created_by__display_name",
    )

    autocomplete_fields = (
        "workspace",
        "parent",
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


@admin.register(WorkspaceFile)
class WorkspaceFileAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "display_name",
        "workspace",
        "folder",
        "size_bytes",
        "uploaded_by",
        "deleted_at",
        "created_at",
    )

    list_filter = (
        "deleted_at",
        "created_at",
    )

    search_fields = (
        "display_name",
        "original_name",
        "sha256",
        "workspace__name",
        "workspace__slug",
        "uploaded_by__email",
        "uploaded_by__display_name",
    )

    autocomplete_fields = (
        "workspace",
        "folder",
        "uploaded_by",
        "deleted_by",
    )

    readonly_fields = (
        "id",
        "original_name",
        "content_type",
        "size_bytes",
        "sha256",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )