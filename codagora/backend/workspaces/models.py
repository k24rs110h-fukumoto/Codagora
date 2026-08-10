import uuid

from django.conf import settings
from django.db import models


class Workspace(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        allow_unicode=True,
    )

    description = models.TextField(
        blank=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_workspaces",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="WorkspaceMember",
        related_name="workspaces",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    class Role(models.TextChoices):
        OWNER = (
            "owner",
            "Owner",
        )

        ADMIN = (
            "admin",
            "Admin",
        )

        MEMBER = (
            "member",
            "Member",
        )

        GUEST = (
            "guest",
            "Guest",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    is_active = models.BooleanField(
        default=True,
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
    )

    left_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "user",
                ),
                name=(
                    "unique_workspace_member"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "role",
                ),
                name="ws_member_role_idx",
            ),
            models.Index(
                fields=(
                    "user",
                    "is_active",
                ),
                name="ws_user_active_idx",
            ),
        ]

        ordering = (
            "joined_at",
        )

    def __str__(self):
        return (
            f"{self.workspace.name} - "
            f"{self.user} - "
            f"{self.role}"
        )


class WorkspaceInvitation(models.Model):
    class Role(models.TextChoices):
        ADMIN = (
            "admin",
            "Admin",
        )

        MEMBER = (
            "member",
            "Member",
        )

        GUEST = (
            "guest",
            "Guest",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    token_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=(
            "created_workspace_invitations"
        ),
    )

    expires_at = models.DateTimeField()

    max_uses = models.PositiveIntegerField(
        default=1,
    )

    use_count = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=(
            "revoked_workspace_invitations"
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    max_uses__gte=1,
                ),
                name=(
                    "workspace_invite_max_uses_gte_1"
                ),
            ),
            models.CheckConstraint(
                condition=models.Q(
                    use_count__lte=models.F(
                        "max_uses"
                    ),
                ),
                name=(
                    "workspace_invite_use_count_lte_max"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "is_active",
                ),
                name=(
                    "ws_invite_active_idx"
                ),
            ),
            models.Index(
                fields=(
                    "expires_at",
                ),
                name=(
                    "ws_invite_expiry_idx"
                ),
            ),
        ]

        ordering = (
            "-created_at",
        )

    def __str__(self):
        return (
            f"{self.workspace.name} - "
            f"{self.role}"
        )