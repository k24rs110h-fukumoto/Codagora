from django.contrib import admin

from .models import (
    GitHubConnection,
    GitHubOAuthState,
    WorkspaceGitHubRepository,
)


@admin.register(GitHubConnection)
class GitHubConnectionAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "user",
        "login",
        "github_user_id",
        "last_verified_at",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__display_name",
        "login",
    )

    readonly_fields = (
        "id",
        "user",
        "github_user_id",
        "login",
        "avatar_url",
        "token_type",
        "scope",
        "access_token_expires_at",
        "refresh_token_expires_at",
        "last_verified_at",
        "created_at",
        "updated_at",
    )

    exclude = (
        "access_token_encrypted",
        "refresh_token_encrypted",
    )

    def has_add_permission(
        self,
        request,
    ):
        return False


@admin.register(GitHubOAuthState)
class GitHubOAuthStateAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "user",
        "workspace",
        "expires_at",
        "used_at",
        "created_at",
    )

    readonly_fields = (
        "id",
        "user",
        "workspace",
        "state_hash",
        "expires_at",
        "used_at",
        "created_at",
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


@admin.register(
    WorkspaceGitHubRepository
)
class WorkspaceGitHubRepositoryAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "full_name",
        "workspace",
        "is_primary",
        "is_private",
        "linked_by",
        "last_synced_at",
        "unlinked_at",
    )

    list_filter = (
        "is_primary",
        "is_private",
        "is_archived",
        "unlinked_at",
    )

    search_fields = (
        "full_name",
        "workspace__name",
        "workspace__slug",
        "owner_login",
    )

    autocomplete_fields = (
        "workspace",
        "linked_by",
        "unlinked_by",
    )

    readonly_fields = (
        "id",
        "installation_id",
        "github_repository_id",
        "owner_login",
        "name",
        "full_name",
        "html_url",
        "last_synced_at",
        "created_at",
        "updated_at",
    )