import uuid

from django.conf import settings
from django.db import models


class WorkspacePlace(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="places",
    )

    name = models.CharField(
        max_length=120,
    )

    description = models.TextField(
        blank=True,
    )

    address = models.CharField(
        max_length=255,
        blank=True,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_workspace_places",
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
        related_name="deleted_workspace_places",
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
            "created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "deleted_at",
                ),
                name="place_ws_deleted_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    latitude__gte=-90,
                    latitude__lte=90,
                ),
                name="place_latitude_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    longitude__gte=-180,
                    longitude__lte=180,
                ),
                name="place_longitude_valid",
            ),
        ]

    def __str__(self):
        return (
            f"{self.workspace.name} / "
            f"{self.name}"
        )


class WorkspaceLocationShare(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="location_shares",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_location_shares",
    )

    place = models.ForeignKey(
        WorkspacePlace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_shares",
    )

    label = models.CharField(
        max_length=120,
        blank=True,
    )

    note = models.CharField(
        max_length=255,
        blank=True,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    accuracy_meters = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-started_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "expires_at",
                ),
                name="locshare_ws_expiry_idx",
            ),
            models.Index(
                fields=(
                    "user",
                    "ended_at",
                ),
                name="locshare_user_end_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    latitude__gte=-90,
                    latitude__lte=90,
                ),
                name="locshare_latitude_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    longitude__gte=-180,
                    longitude__lte=180,
                ),
                name="locshare_longitude_valid",
            ),
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "user",
                ),
                condition=models.Q(
                    ended_at__isnull=True,
                ),
                name="unique_open_location_share",
            ),
        ]

    def __str__(self):
        return (
            f"{self.workspace.name} / "
            f"{self.user}"
        )