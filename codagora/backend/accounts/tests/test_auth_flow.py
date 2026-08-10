from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse

from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import (
    AccountStatus,
    LegalDocumentAcceptance,
    LegalDocumentType,
)


User = get_user_model()


class FirebaseBootstrapApiTests(
    APITestCase,
):
    @patch(
        "accounts.auth_views."
        "sync_firebase_user"
    )
    @patch(
        "accounts.authentication."
        "get_firebase_app"
    )
    @patch(
        "accounts.authentication."
        "auth.verify_id_token"
    )
    def test_google_first_login_creates_provisional_user(
        self,
        mock_verify_id_token,
        mock_get_firebase_app,
        mock_sync_firebase_user,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_verify_id_token.return_value = {
            "uid": "google-user-uid",
            "email": (
                "google@example.com"
            ),
            "email_verified": True,
            "name": "Google User",
            "picture": "",
            "firebase": {
                "sign_in_provider": (
                    "google.com"
                ),
            },
        }

        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:bootstrap"
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=(
                "Bearer test-token"
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user = User.objects.get(
            firebase_uid=(
                "google-user-uid"
            ),
        )

        self.assertEqual(
            user.account_status,
            AccountStatus.PROVISIONAL,
        )

        self.assertEqual(
            user.email,
            "google@example.com",
        )

        self.assertTrue(
            user.email_verified
        )

        self.assertTrue(
            response.data[
                "onboarding_required"
            ]
        )

        self.assertEqual(
            response.data[
                "requirements"
            ][
                "sign_in_provider"
            ],
            "google.com",
        )

    @patch(
        "accounts.auth_views."
        "sync_firebase_user"
    )
    @patch(
        "accounts.authentication."
        "get_firebase_app"
    )
    @patch(
        "accounts.authentication."
        "auth.verify_id_token"
    )
    def test_github_without_email_requires_email_setup(
        self,
        mock_verify_id_token,
        mock_get_firebase_app,
        mock_sync_firebase_user,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_verify_id_token.return_value = {
            "uid": "github-user-uid",
            "firebase": {
                "sign_in_provider": (
                    "github.com"
                ),
            },
        }

        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:bootstrap"
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=(
                "Bearer github-token"
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data[
                "requirements"
            ][
                "email_present"
            ]
        )

        self.assertFalse(
            response.data[
                "requirements"
            ][
                "email_verified"
            ]
        )

    @patch(
        "accounts.auth_views."
        "sync_firebase_user"
    )
    @patch(
        "accounts.authentication."
        "get_firebase_app"
    )
    @patch(
        "accounts.authentication."
        "auth.verify_id_token"
    )
    def test_phone_first_login_requires_email_setup(
        self,
        mock_verify_id_token,
        mock_get_firebase_app,
        mock_sync_firebase_user,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_verify_id_token.return_value = {
            "uid": "phone-user-uid",
            "phone_number": (
                "+819012345678"
            ),
            "firebase": {
                "sign_in_provider": (
                    "phone"
                ),
            },
        }

        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:bootstrap"
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=(
                "Bearer phone-token"
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user = User.objects.get(
            firebase_uid=(
                "phone-user-uid"
            ),
        )

        self.assertTrue(
            user.phone_verified
        )

        self.assertFalse(
            response.data[
                "requirements"
            ][
                "email_present"
            ]
        )

    @patch(
        "accounts.authentication."
        "get_firebase_app"
    )
    @patch(
        "accounts.authentication."
        "auth.verify_id_token"
    )
    def test_same_email_is_not_automatically_linked(
        self,
        mock_verify_id_token,
        mock_get_firebase_app,
    ):
        existing_user = (
            User.objects.create_user(
                email=(
                    "same@example.com"
                ),
                password=(
                    "test-password-123"
                ),
                display_name=(
                    "Existing User"
                ),
            )
        )

        mock_get_firebase_app.return_value = (
            object()
        )

        mock_verify_id_token.return_value = {
            "uid": (
                "different-firebase-uid"
            ),
            "email": (
                "same@example.com"
            ),
            "email_verified": True,
            "firebase": {
                "sign_in_provider": (
                    "google.com"
                ),
            },
        }

        response = self.client.post(
            reverse(
                "auth:bootstrap"
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=(
                "Bearer test-token"
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        existing_user.refresh_from_db()

        self.assertIsNone(
            existing_user.firebase_uid
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

    @patch(
        "accounts.auth_views."
        "sync_firebase_user"
    )
    @patch(
        "accounts.authentication."
        "get_firebase_app"
    )
    @patch(
        "accounts.authentication."
        "auth.verify_id_token"
    )
    def test_anonymous_login_creates_provisional_guest(
        self,
        mock_verify_id_token,
        mock_get_firebase_app,
        mock_sync_firebase_user,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_verify_id_token.return_value = {
            "uid": (
                "anonymous-user-uid"
            ),
            "firebase": {
                "sign_in_provider": (
                    "anonymous"
                ),
            },
        }

        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:bootstrap"
            ),
            {},
            format="json",
            HTTP_AUTHORIZATION=(
                "Bearer anonymous-token"
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user = User.objects.get(
            firebase_uid=(
                "anonymous-user-uid"
            ),
        )

        self.assertTrue(
            user.is_anonymous_account
        )

        self.assertEqual(
            user.account_status,
            AccountStatus.PROVISIONAL,
        )

        self.assertTrue(
            response.data[
                "requirements"
            ][
                "anonymous_upgrade_required"
            ]
        )


class OnboardingApiTests(
    APITestCase,
):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email=(
                    "new@example.com"
                ),
                password=None,
                firebase_uid=(
                    "firebase-new-user"
                ),
                email_verified=True,
                display_name="",
                account_status=(
                    AccountStatus
                    .PROVISIONAL
                ),
            )
        )

        self.decoded_token = {
            "uid": (
                "firebase-new-user"
            ),
            "email": (
                "new@example.com"
            ),
            "email_verified": True,
            "auth_time": 1,
            "firebase": {
                "sign_in_provider": (
                    "google.com"
                ),
            },
        }

        self.client.force_authenticate(
            user=self.user,
            token=self.decoded_token,
        )

    @patch(
        "accounts.auth_services."
        "sync_firebase_user"
    )
    def test_user_can_complete_onboarding(
        self,
        mock_sync_firebase_user,
    ):
        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:"
                "onboarding-complete"
            ),
            {
                "display_name": (
                    "Haruto"
                ),
                "handle": (
                    "haruto_dev"
                ),
                "accept_terms": True,
                "accept_privacy": True,
            },
            format="json",
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

        self.assertEqual(
            self.user.handle,
            "haruto_dev",
        )

        self.assertIsNotNone(
            self.user
            .onboarding_completed_at
        )

        self.assertTrue(
            LegalDocumentAcceptance
            .objects
            .filter(
                user=self.user,
                document_type=(
                    LegalDocumentType
                    .TERMS
                ),
            )
            .exists()
        )

        self.assertTrue(
            LegalDocumentAcceptance
            .objects
            .filter(
                user=self.user,
                document_type=(
                    LegalDocumentType
                    .PRIVACY
                ),
            )
            .exists()
        )

    @patch(
        "accounts.auth_services."
        "sync_firebase_user"
    )
    def test_unverified_email_cannot_complete_onboarding(
        self,
        mock_sync_firebase_user,
    ):
        self.user.email_verified = False

        self.user.save(
            update_fields=(
                "email_verified",
            )
        )

        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:"
                "onboarding-complete"
            ),
            {
                "display_name": (
                    "Haruto"
                ),
                "handle": (
                    "haruto_dev"
                ),
                "accept_terms": True,
                "accept_privacy": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @patch(
        "accounts.auth_services."
        "sync_firebase_user"
    )
    def test_anonymous_user_cannot_complete_onboarding(
        self,
        mock_sync_firebase_user,
    ):
        self.user.is_anonymous_account = (
            True
        )

        self.user.save(
            update_fields=(
                "is_anonymous_account",
            )
        )

        mock_sync_firebase_user.return_value = (
            None
        )

        response = self.client.post(
            reverse(
                "auth:"
                "onboarding-complete"
            ),
            {
                "display_name": (
                    "Guest"
                ),
                "handle": (
                    "guest_user"
                ),
                "accept_terms": True,
                "accept_privacy": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )