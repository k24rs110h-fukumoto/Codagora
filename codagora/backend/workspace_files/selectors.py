from .models import (
    WorkspaceFile,
    WorkspaceFolder,
)


def get_workspace_folders(
    *,
    workspace,
    parent=None,
):
    return (
        WorkspaceFolder.objects
        .filter(
            workspace=workspace,
            parent=parent,
            deleted_at__isnull=True,
        )
        .select_related(
            "created_by",
            "parent",
        )
        .order_by(
            "name",
            "id",
        )
    )


def get_workspace_files(
    *,
    workspace,
    folder=None,
):
    return (
        WorkspaceFile.objects
        .filter(
            workspace=workspace,
            folder=folder,
            deleted_at__isnull=True,
        )
        .select_related(
            "uploaded_by",
            "folder",
        )
        .order_by(
            "display_name",
            "id",
        )
    )


def get_deleted_workspace_folders(
    *,
    workspace,
):
    return (
        WorkspaceFolder.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=False,
        )
        .select_related(
            "created_by",
            "deleted_by",
            "parent",
        )
        .order_by(
            "-deleted_at",
        )
    )


def get_deleted_workspace_files(
    *,
    workspace,
):
    return (
        WorkspaceFile.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=False,
        )
        .select_related(
            "uploaded_by",
            "deleted_by",
            "folder",
        )
        .order_by(
            "-deleted_at",
        )
    )