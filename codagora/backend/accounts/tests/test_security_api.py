from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import (
    AccountStatus,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class SecurityApiTests(
    APITestCase,
):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email=(
                    "secure@example.com"
                ),
                password=None,
                firebase_uid=(
                    "secure-firebase-uid"
                ),
                email_verified=True,
                display_name=(
                    "Secure User"
                ),
                handle=(
                    "secure_user"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.recent_token = {
            "uid": (
                self.user.firebase_uid
            ),
            "auth_time": int(
                timezone.now()
                .timestamp()
            ),
            "firebase": {
                "sign_in_provider": (
                    "google.com"
                ),
                "sign_in_second_factor": (
                    "phone"
                ),
            },
        }

        self.client.force_authenticate(
            user=self.user,
            token=self.recent_token,
        )

    def make_firebase_user(
        self,
        *,
        providers=None,
    ):
        if providers is None:
            providers = [
                "google.com",
                "github.com",
            ]

        return SimpleNamespace(
            email=self.user.email,
            email_verified=True,
            phone_number=(
                "+819012345678"
            ),
            display_name=(
                self.user.display_name
            ),
            photo_url="",
            provider_data=[
                SimpleNamespace(
                    provider_id=(
                        provider
                    ),
                )
                for provider
                in providers
            ],
        )

    @patch(
        "accounts.security_services."
        "get_firebase_app"
    )
    @patch(
        "accounts.security_services."
        "auth.get_user"
    )
    def test_security_overview(
        self,
        mock_get_user,
        mock_get_firebase_app,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_get_user.return_value = (
            self.make_firebase_user()
        )

        response = self.client.get(
            reverse(
                "auth:security"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data[
                "current_provider"
            ],
            "google.com",
        )

        self.assertTrue(
            response.data[
                "mfa_used_current_session"
            ]
        )

        self.assertEqual(
            len(
                response.data[
                    "providers"
                ]
            ),
            2,
        )

    @patch(
        "accounts.security_services."
        "get_firebase_app"
    )
    @patch(
        "accounts.security_services."
        "auth.get_user"
    )
    def test_last_provider_cannot_be_unlinked(
        self,
        mock_get_user,
        mock_get_firebase_app,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_get_user.return_value = (
            self.make_firebase_user(
                providers=[
                    "google.com",
                ]
            )
        )

        response = self.client.post(
            reverse(
                "auth:provider-unlink"
            ),
            {
                "provider_id": (
                    "google.com"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @patch(
        "accounts.security_services."
        "sync_user_from_firebase_record"
    )
    @patch(
        "accounts.security_services."
        "auth.update_user"
    )
    @patch(
        "accounts.security_services."
        "auth.get_user"
    )
    @patch(
        "accounts.security_services."
        "get_firebase_app"
    )
    def test_provider_can_be_unlinked(
        self,
        mock_get_firebase_app,
        mock_get_user,
        mock_update_user,
        mock_sync_user,
    ):
        firebase_app = object()

        mock_get_firebase_app.return_value = (
            firebase_app
        )

        mock_get_user.return_value = (
            self.make_firebase_user()
        )

        mock_update_user.return_value = (
            self.make_firebase_user(
                providers=[
                    "google.com",
                ]
            )
        )

        response = self.client.post(
            reverse(
                "auth:provider-unlink"
            ),
            {
                "provider_id": (
                    "github.com"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_update_user.assert_called_once_with(
            self.user.firebase_uid,
            providers_to_delete=[
                "github.com",
            ],
            app=firebase_app,
        )

        mock_sync_user.assert_called_once()

    def test_stale_auth_cannot_request_account_deletion(
        self,
    ):
        stale_token = {
            "uid": (
                self.user.firebase_uid
            ),
            "auth_time": int(
                (
                    timezone.now()
                    - timedelta(
                        minutes=30
                    )
                )
                .timestamp()
            ),
            "firebase": {
                "sign_in_provider": (
                    "google.com"
                ),
            },
        }

        self.client.force_authenticate(
            user=self.user,
            token=stale_token,
        )

        response = self.client.post(
            reverse(
                "auth:"
                "account-deletion-request"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @patch(
        "accounts.security_services."
        "get_firebase_app"
    )
    @patch(
        "accounts.security_services."
        "auth.revoke_refresh_tokens"
    )
    def test_user_can_request_account_deletion(
        self,
        mock_revoke_refresh_tokens,
        mock_get_firebase_app,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        response = self.client.post(
            reverse(
                "auth:"
                "account-deletion-request"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.account_status,
            AccountStatus
            .DELETION_PENDING,
        )

        self.assertEqual(
            self.user
            .deletion_previous_status,
            AccountStatus.ACTIVE,
        )

        self.assertIsNotNone(
            self.user
            .deletion_requested_at
        )

        self.assertIsNotNone(
            self.user
            .deletion_scheduled_for
        )

        mock_revoke_refresh_tokens.assert_called_once()

    def test_workspace_owner_cannot_delete_account(
        self,
    ):
        create_workspace(
            owner=self.user,
            name="Owned Workspace",
        )

        response = self.client.post(
            reverse(
                "auth:"
                "account-deletion-request"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_can_cancel_account_deletion(
        self,
    ):
        self.user.account_status = (
            AccountStatus
            .DELETION_PENDING
        )

        self.user.deletion_previous_status = (
            AccountStatus.ACTIVE
        )

        self.user.deletion_requested_at = (
            timezone.now()
        )

        self.user.deletion_scheduled_for = (
            timezone.now()
            + timedelta(days=7)
        )

        self.user.save(
            update_fields=(
                "account_status",
                "deletion_previous_status",
                "deletion_requested_at",
                "deletion_scheduled_for",
            )
        )

        response = self.client.post(
            reverse(
                "auth:"
                "account-deletion-cancel"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.account_status,
            AccountStatus.ACTIVE,
        )

        self.assertIsNone(
            self.user
            .deletion_requested_at
        )

        self.assertIsNone(
            self.user
            .deletion_scheduled_for
        )

    @patch(
        "accounts.security_services."
        "get_firebase_app"
    )
    @patch(
        "accounts.security_services."
        "auth.revoke_refresh_tokens"
    )
    def test_user_can_revoke_all_sessions(
        self,
        mock_revoke_refresh_tokens,
        mock_get_firebase_app,
    ):
        firebase_app = object()

        mock_get_firebase_app.return_value = (
            firebase_app
        )

        response = self.client.post(
            reverse(
                "auth:revoke-sessions"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        mock_revoke_refresh_tokens.assert_called_once_with(
            self.user.firebase_uid,
            app=firebase_app,
        )