from django.urls import path

from .views import (
    GitHubConnectStartView,
    GitHubInstallationListView,
    GitHubInstallationRepositoryListView,
    WorkspaceGitHubOverviewView,
    WorkspaceGitHubRepositoryDetailView,
    WorkspaceGitHubRepositoryListLinkView,
    WorkspaceGitHubRepositoryOverviewView,
    WorkspaceGitHubRepositoryPrimaryView,
    WorkspaceGitHubRepositorySyncView,
)


app_name = "github"


urlpatterns = [
    path(
        "",
        WorkspaceGitHubOverviewView.as_view(),
        name="overview",
    ),

    path(
        "connect/",
        GitHubConnectStartView.as_view(),
        name="connect-start",
    ),

    path(
        "installations/",
        GitHubInstallationListView.as_view(),
        name="installation-list",
    ),

    path(
        (
            "installations/"
            "<int:installation_id>/"
            "repositories/"
        ),
        GitHubInstallationRepositoryListView.as_view(),
        name=(
            "installation-repository-list"
        ),
    ),

    path(
        "repositories/",
        WorkspaceGitHubRepositoryListLinkView.as_view(),
        name="repository-list-link",
    ),

    path(
        (
            "repositories/"
            "<uuid:repository_link_id>/"
        ),
        WorkspaceGitHubRepositoryDetailView.as_view(),
        name="repository-detail",
    ),

    path(
        (
            "repositories/"
            "<uuid:repository_link_id>/"
            "primary/"
        ),
        WorkspaceGitHubRepositoryPrimaryView.as_view(),
        name="repository-primary",
    ),

    path(
        (
            "repositories/"
            "<uuid:repository_link_id>/"
            "sync/"
        ),
        WorkspaceGitHubRepositorySyncView.as_view(),
        name="repository-sync",
    ),

    path(
        (
            "repositories/"
            "<uuid:repository_link_id>/"
            "overview/"
        ),
        WorkspaceGitHubRepositoryOverviewView.as_view(),
        name="repository-overview",
    ),
]