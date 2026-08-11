from urllib.parse import (
    parse_qs,
    urlsplit,
)
from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.core.exceptions import (
    ValidationError,
)
from django.test import (
    TestCase,
    override_settings,
)

from integrations.models import (
    GitHubOAuthState,
)
from integrations.services import (
    create_github_oauth_state,
    verify_installation_for_user,
)
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)


User = get_user_model()


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
    ],
    DEBUG=True,
    GITHUB_APP_CLIENT_ID=(
        "test-client-id"
    ),
    GITHUB_APP_CALLBACK_URL=(
        "http://127.0.0.1:8000/"
        "api/v1/integrations/"
        "github/callback/"
    ),
    GITHUB_APP_MOBILE_REDIRECT_URL="",
)
class GitHubOAuthHardeningTests(
    TestCase
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email=(
                    "github-owner@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.admin = (
            User.objects.create_user(
                email=(
                    "github-admin@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.workspace = (
            Workspace.objects.create(
                name=(
                    "GitHub Hardening"
                ),
                slug=(
                    "github-hardening"
                ),
                owner=self.owner,
            )
        )

        self.admin_membership = (
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=self.admin,
                role=(
                    WorkspaceMember
                    .Role
                    .ADMIN
                ),
                is_active=True,
            )
        )

    def create_state(
        self,
        *,
        user=None,
        installation_id=None,
    ):
        state, raw_state = (
            create_github_oauth_state(
                workspace=self.workspace,
                user=(
                    user
                    or self.owner
                ),
                lifetime_minutes=10,
            )
        )

        if installation_id:
            state.installation_id = (
                installation_id
            )

            state.save(
                update_fields=(
                    "installation_id",
                )
            )

        return (
            state,
            raw_state,
        )

    def test_setup_attaches_installation(
        self,
    ):
        state, raw_state = (
            self.create_state()
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/setup/"
            ),
            {
                "state": raw_state,
                "installation_id": "123",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        state.refresh_from_db()

        self.assertEqual(
            state.installation_id,
            123,
        )

        location = (
            response["Location"]
        )

        parsed = urlsplit(
            location
        )

        self.assertEqual(
            parsed.scheme,
            "https",
        )

        self.assertEqual(
            parsed.netloc,
            "github.com",
        )

        query = parse_qs(
            parsed.query
        )

        self.assertEqual(
            query[
                "client_id"
            ][0],
            "test-client-id",
        )

        self.assertEqual(
            query[
                "state"
            ][0],
            raw_state,
        )

    def test_setup_rejects_invalid_installation_id(
        self,
    ):
        state, raw_state = (
            self.create_state()
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/setup/"
            ),
            {
                "state": raw_state,
                "installation_id": (
                    "not-a-number"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        state.refresh_from_db()

        self.assertIsNone(
            state.installation_id
        )

    @patch(
        "integrations.views."
        "complete_github_connection"
    )
    def test_callback_success(
        self,
        complete_mock,
    ):
        state, raw_state = (
            self.create_state(
                installation_id=123,
            )
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/callback/"
            ),
            {
                "state": raw_state,
                "code": (
                    "github-code"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()[
                "status"
            ],
            "success",
        )

        complete_mock.assert_called_once()

        state.refresh_from_db()

        self.assertIsNotNone(
            state.used_at
        )

    @patch(
    "integrations.views."
    "complete_github_connection"
    )
    def test_callback_allows_connection_without_installation(
        self,
        complete_mock,
    ):
        state, raw_state = (
            self.create_state()
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/callback/"
            ),
            {
                "state": raw_state,
                "code": (
                    "github-code"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()[
                "status"
            ],
        "success",
        )

        complete_mock.assert_called_once_with(
            state=state,
            code="github-code",
        )

        state.refresh_from_db()

        self.assertIsNotNone(
            state.used_at
        )

    @patch(
        "integrations.views."
        "complete_github_connection"
    )
    def test_state_cannot_be_replayed(
        self,
        complete_mock,
    ):
        state, raw_state = (
            self.create_state(
                installation_id=123,
            )
        )

        first_response = (
            self.client.get(
                (
                    "/api/v1/integrations/"
                    "github/callback/"
                ),
                {
                    "state": raw_state,
                    "code": (
                        "first-code"
                    ),
                },
            )
        )

        second_response = (
            self.client.get(
                (
                    "/api/v1/integrations/"
                    "github/callback/"
                ),
                {
                    "state": raw_state,
                    "code": (
                        "second-code"
                    ),
                },
            )
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertEqual(
            complete_mock.call_count,
            1,
        )

        state.refresh_from_db()

        self.assertIsNotNone(
            state.used_at
        )

    @patch(
        "integrations.views."
        "complete_github_connection"
    )
    def test_downgraded_admin_cannot_complete_connection(
        self,
        complete_mock,
    ):
        state, raw_state = (
            self.create_state(
                user=self.admin,
                installation_id=123,
            )
        )

        self.admin_membership.role = (
            WorkspaceMember.Role.GUEST
        )

        self.admin_membership.save(
            update_fields=(
                "role",
            )
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/callback/"
            ),
            {
                "state": raw_state,
                "code": (
                    "github-code"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        complete_mock.assert_not_called()

        state.refresh_from_db()

        self.assertIsNotNone(
            state.used_at
        )

    def test_authorization_denied_consumes_state(
        self,
    ):
        state, raw_state = (
            self.create_state(
                installation_id=123,
            )
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/callback/"
            ),
            {
                "state": raw_state,
                "error": (
                    "access_denied"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()[
                "code"
            ],
            "authorization_denied",
        )

        state.refresh_from_db()

        self.assertIsNotNone(
            state.used_at
        )

    @override_settings(
        GITHUB_APP_MOBILE_REDIRECT_URL=(
            "codagora://github/complete"
        )
    )
    @patch(
        "integrations.views."
        "complete_github_connection"
    )
    def test_custom_scheme_mobile_redirect(
        self,
        complete_mock,
    ):
        _, raw_state = (
            self.create_state(
                installation_id=123,
            )
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/callback/"
            ),
            {
                "state": raw_state,
                "code": (
                    "github-code"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        parsed = urlsplit(
            response[
                "Location"
            ]
        )

        self.assertEqual(
            parsed.scheme,
            "codagora",
        )

        self.assertEqual(
            parsed.netloc,
            "github",
        )

        query = parse_qs(
            parsed.query
        )

        self.assertEqual(
            query[
                "status"
            ][0],
            "success",
        )

        self.assertEqual(
            query[
                "workspace"
            ][0],
            self.workspace.slug,
        )

    @override_settings(
        GITHUB_APP_MOBILE_REDIRECT_URL=(
            "javascript://example"
        )
    )
    @patch(
        "integrations.views."
        "complete_github_connection"
    )
    def test_unsafe_mobile_redirect_is_rejected(
        self,
        complete_mock,
    ):
        _, raw_state = (
            self.create_state(
                installation_id=123,
            )
        )

        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/callback/"
            ),
            {
                "state": raw_state,
                "code": (
                    "github-code"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()[
                "status"
            ],
            "success",
        )

    @patch(
        "integrations.services."
        "list_user_installations"
    )
    def test_spoofed_installation_is_rejected(
        self,
        installations_mock,
    ):
        installations_mock.return_value = [
            {
                "id": 123,
            }
        ]

        with self.assertRaises(
            ValidationError
        ):
            verify_installation_for_user(
                access_token=(
                    "fake-token"
                ),
                installation_id=999,
            )

    @patch(
        "integrations.services."
        "list_user_installations"
    )
    def test_owned_installation_is_accepted(
        self,
        installations_mock,
    ):
        installations_mock.return_value = [
            {
                "id": 123,
            }
        ]

        installation = (
            verify_installation_for_user(
                access_token=(
                    "fake-token"
                ),
                installation_id=123,
            )
        )

        self.assertEqual(
            installation[
                "id"
            ],
            123,
        )