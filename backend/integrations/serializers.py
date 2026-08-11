from rest_framework import serializers

from workspaces.serializers import (
    WorkspaceUserSummarySerializer,
)

from .models import (
    GitHubConnection,
    WorkspaceGitHubRepository,
)


class GitHubConnectionSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = GitHubConnection

        fields = (
            "id",
            "github_user_id",
            "login",
            "avatar_url",
            "last_verified_at",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class WorkspaceGitHubRepositorySerializer(
    serializers.ModelSerializer,
):
    linked_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = (
            WorkspaceGitHubRepository
        )

        fields = (
            "id",
            "installation_id",
            "github_repository_id",
            "owner_login",
            "name",
            "full_name",
            "description",
            "html_url",
            "default_branch",
            "is_private",
            "is_archived",
            "is_primary",
            "stargazers_count",
            "forks_count",
            "open_issues_count",
            "pushed_at",
            "linked_by",
            "last_synced_at",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class GitHubInstallationSerializer(
    serializers.Serializer,
):
    id = (
        serializers.IntegerField()
    )

    account_login = (
        serializers.CharField()
    )

    account_type = (
        serializers.CharField()
    )

    avatar_url = (
        serializers.URLField(
            allow_blank=True,
        )
    )

    repository_selection = (
        serializers.CharField(
            allow_blank=True,
        )
    )

    permissions = serializers.DictField()


class GitHubRemoteRepositorySerializer(
    serializers.Serializer,
):
    id = (
        serializers.IntegerField()
    )

    name = serializers.CharField()

    full_name = (
        serializers.CharField()
    )

    private = (
        serializers.BooleanField()
    )

    html_url = (
        serializers.URLField()
    )

    description = (
        serializers.CharField(
            allow_blank=True,
        )
    )

    default_branch = (
        serializers.CharField(
            allow_blank=True,
        )
    )

    archived = (
        serializers.BooleanField()
    )

    permissions = (
        serializers.DictField()
    )


class GitHubRepositoryLinkSerializer(
    serializers.Serializer,
):
    installation_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )

    repository_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )

    is_primary = (
        serializers.BooleanField(
            default=False,
        )
    )