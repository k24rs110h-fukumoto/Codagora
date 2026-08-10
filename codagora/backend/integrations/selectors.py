from .models import (
    GitHubConnection,
    WorkspaceGitHubRepository,
)


def get_github_connection(
    *,
    user,
):
    return (
        GitHubConnection.objects
        .filter(
            user=user,
        )
        .first()
    )


def get_workspace_github_repositories(
    *,
    workspace,
):
    return (
        WorkspaceGitHubRepository.objects
        .filter(
            workspace=workspace,
            unlinked_at__isnull=True,
        )
        .select_related(
            "linked_by",
        )
        .order_by(
            "-is_primary",
            "full_name",
        )
    )