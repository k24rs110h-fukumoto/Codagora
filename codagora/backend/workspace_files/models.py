import uuid

from pathlib import Path

from django.conf import settings
from django.db import models


def workspace_file_upload_to(
    instance,
    filename,
):
    suffix = (
        Path(filename)
        .suffix
        .lower()[:20]
    )

    return (
        "workspace_files/"
        f"{instance.workspace_id}/"
        f"{instance.id}/"
        f"content{suffix}"
    )


class WorkspaceFolder(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="folders",
    )

    name = models.CharField(
        max_length=255,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_workspace_folders",
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_workspace_folders",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "name",
            "id",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "parent",
                ),
                name="wsfolder_ws_parent_idx",
            ),
            models.Index(
                fields=(
                    "workspace",
                    "deleted_at",
                ),
                name="wsfolder_deleted_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "name",
                ),
                condition=models.Q(
                    parent__isnull=True,
                    deleted_at__isnull=True,
                ),
                name="unique_active_root_folder",
            ),
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "parent",
                    "name",
                ),
                condition=models.Q(
                    parent__isnull=False,
                    deleted_at__isnull=True,
                ),
                name="unique_active_child_folder",
            ),
        ]

    def __str__(self):
        return self.name


class WorkspaceFile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="workspace_files",
    )

    folder = models.ForeignKey(
        WorkspaceFolder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="files",
    )

    file = models.FileField(
        upload_to=workspace_file_upload_to,
        max_length=500,
    )

    original_name = models.CharField(
        max_length=255,
    )

    display_name = models.CharField(
        max_length=255,
    )

    content_type = models.CharField(
        max_length=255,
        blank=True,
    )

    size_bytes = models.PositiveBigIntegerField(
        default=0,
    )

    sha256 = models.CharField(
        max_length=64,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_workspace_files",
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_workspace_files",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "display_name",
            "id",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "folder",
                ),
                name="wsfile_ws_folder_idx",
            ),
            models.Index(
                fields=(
                    "workspace",
                    "deleted_at",
                ),
                name="wsfile_deleted_idx",
            ),
            models.Index(
                fields=(
                    "sha256",
                ),
                name="wsfile_sha256_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "display_name",
                ),
                condition=models.Q(
                    folder__isnull=True,
                    deleted_at__isnull=True,
                ),
                name="unique_active_root_file",
            ),
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "folder",
                    "display_name",
                ),
                condition=models.Q(
                    folder__isnull=False,
                    deleted_at__isnull=True,
                ),
                name="unique_active_folder_file",
            ),
        ]

    def __str__(self):
        return self.display_name