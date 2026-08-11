import re
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from integrations.github_client import (
    exchange_code_for_user_token,
)
from integrations.services import (
    build_github_pkce_challenge,
    build_github_pkce_verifier,
    complete_github_connection,
    create_github_oauth_state,
)
from workspaces.models import Workspace


User = get_user_model()


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    DEBUG=True,
    GITHUB_APP_CLIENT_ID="test-client-id",
    GITHUB_APP_CLIENT_SECRET="test-client-secret",
    GITHUB_APP_CALLBACK_URL=(
        "http://127.0.0.1:8000/"
        "api/v1/integrations/github/callback/"
    ),
)
class GitHubPKCETests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="github-pkce@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="GitHub PKCE",
            slug="github-pkce",
            owner=self.user,
        )

    def test_pkce_verifier_and_challenge_are_s256_values(
        self,
    ):
        state, _ = create_github_oauth_state(
            workspace=self.workspace,
            user=self.user,
            lifetime_minutes=10,
        )

        verifier = build_github_pkce_verifier(
            state
        )

        challenge = build_github_pkce_challenge(
            state
        )

        self.assertEqual(
            len(verifier),
            43,
        )

        self.assertEqual(
            len(challenge),
            43,
        )

        allowed = re.compile(
            r"^[A-Za-z0-9_-]{43}$"
        )

        self.assertRegex(
            verifier,
            allowed,
        )

        self.assertRegex(
            challenge,
            allowed,
        )

        self.assertNotEqual(
            verifier,
            challenge,
        )

    def test_setup_authorization_url_contains_pkce(
        self,
    ):
        state, raw_state = (
            create_github_oauth_state(
                workspace=self.workspace,
                user=self.user,
                lifetime_minutes=10,
            )
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

        parsed = urlsplit(
            response["Location"]
        )

        query = parse_qs(
            parsed.query
        )

        self.assertEqual(
            query[
                "code_challenge_method"
            ][0],
            "S256",
        )

        self.assertEqual(
            query[
                "code_challenge"
            ][0],
            build_github_pkce_challenge(
                state
            ),
        )

        self.assertEqual(
            query["state"][0],
            raw_state,
        )

    @override_settings(
        GITHUB_APP_MOBILE_REDIRECT_URL=(
            "codagora://github/complete"
        ),
    )
    def test_setup_update_without_state_returns_success(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/setup/"
            ),
            {
                "installation_id": "123",
                "setup_action": "update",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        parsed = urlsplit(
            response["Location"]
        )

        query = parse_qs(
            parsed.query
        )

        self.assertEqual(
            parsed.scheme,
            "codagora",
        )

        self.assertEqual(
            query["status"][0],
            "success",
        )

    def test_setup_without_state_is_rejected_when_not_update(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/setup/"
            ),
            {
                "installation_id": "123",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["code"],
            "invalid_setup",
        )

    def test_setup_update_rejects_invalid_installation_id(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/integrations/"
                "github/setup/"
            ),
            {
                "installation_id": "invalid",
                "setup_action": "update",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["code"],
            "invalid_setup",
        )

    @patch(
        "integrations.services."
        "save_github_connection"
    )
    @patch(
        "integrations.services."
        "verify_installation_for_user"
    )
    @patch(
        "integrations.services."
        "get_authenticated_github_user"
    )
    @patch(
        "integrations.services."
        "exchange_code_for_user_token"
    )
    def test_complete_connection_uses_pkce_verifier(
        self,
        exchange_mock,
        github_user_mock,
        verify_installation_mock,
        save_connection_mock,
    ):
        state, _ = (
            create_github_oauth_state(
                workspace=self.workspace,
                user=self.user,
                lifetime_minutes=10,
            )
        )

        state.installation_id = 123
        state.save(
            update_fields=(
                "installation_id",
            )
        )

        exchange_mock.return_value = {
            "access_token": "token",
        }

        github_user_mock.return_value = {
            "id": 1,
            "login": "octocat",
        }

        sentinel_connection = object()

        save_connection_mock.return_value = (
            sentinel_connection
        )

        result = complete_github_connection(
            state=state,
            code="github-code",
        )

        exchange_mock.assert_called_once_with(
            code="github-code",
            code_verifier=(
                build_github_pkce_verifier(
                    state
                )
            ),
        )

        verify_installation_mock.assert_called_once_with(
            access_token="token",
            installation_id=123,
        )

        self.assertIs(
            result,
            sentinel_connection,
        )

    @patch(
        "integrations.services."
        "save_github_connection"
    )
    @patch(
        "integrations.services."
        "get_authenticated_github_user"
    )
    @patch(
        "integrations.services."
        "exchange_code_for_user_token"
    )
    def test_legacy_state_without_setup_keeps_compatibility(
        self,
        exchange_mock,
        github_user_mock,
        save_connection_mock,
    ):
        state, _ = (
            create_github_oauth_state(
                workspace=self.workspace,
                user=self.user,
                lifetime_minutes=10,
            )
        )

        exchange_mock.return_value = {
            "access_token": "token",
        }

        github_user_mock.return_value = {
            "id": 1,
            "login": "octocat",
        }

        save_connection_mock.return_value = object()

        complete_github_connection(
            state=state,
            code="github-code",
        )

        exchange_mock.assert_called_once_with(
            code="github-code",
        )

    @patch(
        "integrations.github_client."
        "requests.post"
    )
    def test_token_exchange_sends_code_verifier(
        self,
        post_mock,
    ):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "access_token": "token",
            "token_type": "bearer",
        }

        post_mock.return_value = response

        payload = (
            exchange_code_for_user_token(
                code="github-code",
                code_verifier=(
                    "a" * 43
                ),
            )
        )

        self.assertEqual(
            payload["access_token"],
            "token",
        )

        sent_data = (
            post_mock.call_args.kwargs[
                "data"
            ]
        )

        self.assertEqual(
            sent_data[
                "code_verifier"
            ],
            "a" * 43,
        )

        self.assertEqual(
            sent_data[
                "code"
            ],
            "github-code",
        )

    @patch(
        "integrations.github_client."
        "requests.post"
    )
    def test_token_exchange_without_pkce_stays_compatible(
        self,
        post_mock,
    ):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "access_token": "token",
            "token_type": "bearer",
        }

        post_mock.return_value = response

        exchange_code_for_user_token(
            code="github-code",
        )

        sent_data = (
            post_mock.call_args.kwargs[
                "data"
            ]
        )

        self.assertNotIn(
            "code_verifier",
            sent_data,
        )
