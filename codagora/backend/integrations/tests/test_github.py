from unittest.mock import patch

from cryptography.fernet import Fernet

from django.contrib.auth import (
    get_user_model,
)
from django.test import (
    override_settings,
)
from django.urls import reverse

from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import AccountStatus
from integrations.models import (
    GitHubConnection,
    WorkspaceGitHubRepository,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)
from integrations.github_client import (
    GitHubAPIError,
)


User = get_user_model()

TEST_ENCRYPTION_KEY = (
    Fernet.generate_key().decode()
)


@override_settings(
    CODAGORA_TOKEN_ENCRYPTION_KEY=(
        TEST_ENCRYPTION_KEY
    ),
    GITHUB_APP_SLUG="codagora-test",
    GITHUB_APP_CLIENT_ID="test-client",
    GITHUB_APP_CLIENT_SECRET=(
        "test-secret"
    ),
    GITHUB_APP_CALLBACK_URL=(
        "https://example.com/"
        "api/v1/integrations/"
        "github/callback/"
    ),
    GITHUB_APP_MOBILE_REDIRECT_URL="",
)
class GitHubIntegrationTests(
    APITestCase,
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email="gh-owner@example.com",
                password=None,
                firebase_uid="gh-owner",
                display_name="Owner",
                handle="gh_owner",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.admin = (
            User.objects.create_user(
                email="gh-admin@example.com",
                password=None,
                firebase_uid="gh-admin",
                display_name="Admin",
                handle="gh_admin",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.member = (
            User.objects.create_user(
                email="gh-member@example.com",
                password=None,
                firebase_uid="gh-member",
                display_name="Member",
                handle="gh_member",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.guest = (
            User.objects.create_user(
                email="gh-guest@example.com",
                password=None,
                firebase_uid="gh-guest",
                display_name="Guest",
                handle="gh_guest",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="GitHub Workspace",
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.admin,
            role=(
                WorkspaceMember.Role.ADMIN
            ),
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember.Role.MEMBER
            ),
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.guest,
            role=(
                WorkspaceMember.Role.GUEST
            ),
        )

    def connect_url(self):
        return reverse(
            "workspaces:github:"
            "connect-start",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def repository_url(self):
        return reverse(
            "workspaces:github:"
            "repository-list-link",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def create_connection(
        self,
        user,
    ):
        return (
            GitHubConnection.objects
            .create(
                user=user,
                github_user_id=12345,
                login="octocat",
                avatar_url="",
                access_token_encrypted=(
                    Fernet(
                        TEST_ENCRYPTION_KEY
                        .encode()
                    )
                    .encrypt(
                        b"token"
                    )
                    .decode()
                ),
            )
        )

    def test_owner_can_start_connection(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            self.connect_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            (
                "https://github.com/"
                "apps/codagora-test/"
                "installations/new"
            ),
            response.data[
                "authorization_url"
            ],
        )

        self.assertIn(
            "state=",
            response.data[
                "authorization_url"
            ],
        )

    def test_member_cannot_start_connection(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.connect_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guest_cannot_view_github(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.get(
            reverse(
                "workspaces:github:"
                "overview",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_member_can_view_linked_repositories(
        self,
    ):
        WorkspaceGitHubRepository.objects.create(
            workspace=self.workspace,
            installation_id=100,
            github_repository_id=200,
            owner_login="owner",
            name="repo",
            full_name="owner/repo",
            html_url=(
                "https://github.com/owner/repo"
            ),
            linked_by=self.owner,
            is_primary=True,
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.get(
            self.repository_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    @patch(
        "integrations.services."
        "find_user_installation_repository"
    )
    def test_owner_can_link_repository(
        self,
        mocked_repository,
    ):
        mocked_repository.return_value = {
            "id": 200,
            "name": "codagora",
            "full_name": (
                "octocat/codagora"
            ),
            "description": "Test",
            "html_url": (
                "https://github.com/"
                "octocat/codagora"
            ),
            "default_branch": "main",
            "private": True,
            "archived": False,
            "stargazers_count": 1,
            "forks_count": 2,
            "open_issues_count": 3,
            "pushed_at": (
                "2026-08-08T00:00:00Z"
            ),
            "owner": {
                "login": "octocat",
            },
        }

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            self.repository_url(),
            {
                "installation_id": 100,
                "repository_id": 200,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        linked = (
            WorkspaceGitHubRepository
            .objects
            .get(
                workspace=self.workspace,
                github_repository_id=200,
                unlinked_at__isnull=True,
            )
        )

        self.assertTrue(
            linked.is_primary
        )

        self.assertEqual(
            linked.full_name,
            "octocat/codagora",
        )

    @patch(
        "integrations.services."
        "find_user_installation_repository"
    )
    def test_member_cannot_link_repository(
        self,
        mocked_repository,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.repository_url(),
            {
                "installation_id": 100,
                "repository_id": 200,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        mocked_repository.assert_not_called()

    def test_owner_can_unlink_repository(
        self,
    ):
        linked = (
            WorkspaceGitHubRepository
            .objects
            .create(
                workspace=self.workspace,
                installation_id=100,
                github_repository_id=200,
                owner_login="owner",
                name="repo",
                full_name="owner/repo",
                html_url=(
                    "https://github.com/"
                    "owner/repo"
                ),
                linked_by=self.owner,
                is_primary=True,
            )
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.delete(
            reverse(
                "workspaces:github:"
                "repository-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "repository_link_id": (
                        linked.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        linked.refresh_from_db()

        self.assertIsNotNone(
            linked.unlinked_at
        )

        self.assertFalse(
            linked.is_primary
        )

    def test_primary_repository_can_change(
        self,
    ):
        first = (
            WorkspaceGitHubRepository
            .objects
            .create(
                workspace=self.workspace,
                installation_id=100,
                github_repository_id=200,
                owner_login="owner",
                name="one",
                full_name="owner/one",
                html_url=(
                    "https://github.com/"
                    "owner/one"
                ),
                linked_by=self.owner,
                is_primary=True,
            )
        )

        second = (
            WorkspaceGitHubRepository
            .objects
            .create(
                workspace=self.workspace,
                installation_id=100,
                github_repository_id=201,
                owner_login="owner",
                name="two",
                full_name="owner/two",
                html_url=(
                    "https://github.com/"
                    "owner/two"
                ),
                linked_by=self.owner,
            )
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            reverse(
                "workspaces:github:"
                "repository-primary",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "repository_link_id": (
                        second.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(
            first.is_primary
        )

        self.assertTrue(
            second.is_primary
        )

    @patch(
        "integrations.services."
        "get_authenticated_github_user"
    )
    @patch(
        "integrations.services."
        "exchange_code_for_user_token"
    )
    def test_callback_saves_connection(
        self,
        mocked_exchange,
        mocked_user,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        start_response = (
            self.client.post(
                self.connect_url()
            )
        )

        authorization_url = (
            start_response.data[
                "authorization_url"
            ]
        )

        raw_state = (
            authorization_url
            .split(
                "state=",
                1,
            )[1]
        )

        mocked_exchange.return_value = {
            "access_token": "token",
            "token_type": "bearer",
            "scope": "",
        }

        mocked_user.return_value = {
            "id": 999,
            "login": "octocat",
            "avatar_url": (
                "https://example.com/avatar.png"
            ),
        }

        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            reverse(
                "integrations:"
                "github-callback"
            ),
            {
                "state": raw_state,
                "code": "code",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        connection = (
            GitHubConnection.objects
            .get(
                user=self.owner
            )
        )

        self.assertEqual(
            connection.login,
            "octocat",
        )

        self.assertNotEqual(
            connection.access_token_encrypted,
            "token",
        )

    def test_connection_serializer_hides_tokens(
        self,
    ):
        self.create_connection(
            self.owner
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.get(
            reverse(
                "workspaces:github:"
                "overview",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        connection = response.data[
            "connection"
        ]

        self.assertNotIn(
            "access_token_encrypted",
            connection,
        )

        self.assertNotIn(
            "refresh_token_encrypted",
            connection,
        )

@patch(
    "integrations.services.github_request"
)
@patch(
    "integrations.services."
    "get_installation_access_token"
)
def test_empty_repository_overview(
    self,
    mocked_token,
    mocked_request,
):
    linked = (
        WorkspaceGitHubRepository.objects
        .create(
            workspace=self.workspace,
            installation_id=100,
            github_repository_id=200,
            owner_login="owner",
            name="repo",
            full_name="owner/repo",
            html_url=(
                "https://github.com/"
                "owner/repo"
            ),
            linked_by=self.owner,
            is_primary=True,
        )
    )

    mocked_token.return_value = (
        "installation-token"
    )

    def github_response(
        method,
        path,
        **kwargs,
    ):
        if path == "/repos/owner/repo":
            return {
                "id": 200,
                "name": "repo",
                "full_name": "owner/repo",
                "description": "",
                "html_url": (
                    "https://github.com/"
                    "owner/repo"
                ),
                "private": False,
                "archived": False,
                "default_branch": "main",
                "stargazers_count": 0,
                "forks_count": 0,
                "open_issues_count": 0,
                "pushed_at": None,
            }

        if path == (
            "/repos/owner/repo/commits"
        ):
            raise GitHubAPIError(
                "Git Repository is empty.",
                status_code=409,
            )

        if path == (
            "/repos/owner/repo/pulls"
        ):
            return []

        raise AssertionError(
            f"Unexpected path: {path}"
        )

    mocked_request.side_effect = (
        github_response
    )

    self.client.force_authenticate(
        user=self.owner,
    )

    response = self.client.get(
        reverse(
            "workspaces:github:"
            "repository-overview",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
                "repository_link_id": (
                    linked.id
                ),
            },
        )
    )

    self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
    )

    self.assertEqual(
        response.data[
            "recent_commits"
        ],
        [],
    )

    self.assertEqual(
        response.data[
            "open_pull_requests"
        ],
        [],
    )
