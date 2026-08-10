import uuid

from django.conf import settings
from django.db import models


class GitHubConnection(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="github_connection",
    )

    github_user_id = models.PositiveBigIntegerField(
        unique=True,
    )

    login = models.CharField(
        max_length=100,
    )

    avatar_url = models.URLField(
        max_length=500,
        blank=True,
    )

    access_token_encrypted = models.TextField(
        editable=False,
    )

    access_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    refresh_token_encrypted = models.TextField(
        blank=True,
        editable=False,
    )

    refresh_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    token_type = models.CharField(
        max_length=50,
        default="bearer",
    )

    scope = models.CharField(
        max_length=500,
        blank=True,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "login",
        )

    def __str__(self):
        return (
            f"{self.user} / "
            f"{self.login}"
        )


class GitHubOAuthState(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="github_oauth_states",
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="github_oauth_states",
    )

    state_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
    )

    installation_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=(
                    "expires_at",
                    "used_at",
                ),
                name="ghstate_exp_used_idx",
            ),
        ]

    def __str__(self):
        return str(self.id)


class WorkspaceGitHubRepository(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="github_repositories",
    )

    installation_id = models.PositiveBigIntegerField()

    github_repository_id = models.PositiveBigIntegerField()

    owner_login = models.CharField(
        max_length=100,
    )

    name = models.CharField(
        max_length=100,
    )

    full_name = models.CharField(
        max_length=220,
    )

    description = models.TextField(
        blank=True,
    )

    html_url = models.URLField(
        max_length=500,
    )

    default_branch = models.CharField(
        max_length=255,
        blank=True,
    )

    is_private = models.BooleanField(
        default=False,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    stargazers_count = models.PositiveIntegerField(
        default=0,
    )

    forks_count = models.PositiveIntegerField(
        default=0,
    )

    open_issues_count = models.PositiveIntegerField(
        default=0,
    )

    pushed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_github_repositories",
    )

    unlinked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    unlinked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="unlinked_github_repositories",
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-is_primary",
            "full_name",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "unlinked_at",
                ),
                name="ghrepo_ws_active_idx",
            ),
            models.Index(
                fields=(
                    "installation_id",
                ),
                name="ghrepo_install_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "github_repository_id",
                ),
                condition=models.Q(
                    unlinked_at__isnull=True,
                ),
                name="unique_active_workspace_repo",
            ),
            models.UniqueConstraint(
                fields=(
                    "workspace",
                ),
                condition=models.Q(
                    is_primary=True,
                    unlinked_at__isnull=True,
                ),
                name="unique_primary_workspace_repo",
            ),
        ]

    def __str__(self):
        return self.full_name