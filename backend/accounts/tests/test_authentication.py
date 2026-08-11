from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class FirebaseAuthenticationTests(APITestCase):
    @patch(
        "accounts.authentication.get_firebase_app"
    )
    @patch(
        "accounts.authentication.auth.verify_id_token"
    )
    def test_firebase_user_is_created(
        self,
        mock_verify_id_token,
        mock_get_firebase_app,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        mock_verify_id_token.return_value = {
            "uid": "firebase-test-uid",
            "email": "firebase@example.com",
            "name": "Firebase User",
        }

        response = self.client.get(
            reverse("accounts:me"),
            HTTP_AUTHORIZATION=(
                "Bearer test-token"
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            User.objects.filter(
                firebase_uid=(
                    "firebase-test-uid"
                )
            ).exists()
        )

    def test_invalid_bearer_header_is_rejected(
        self,
    ):
        response = self.client.get(
            reverse("accounts:me"),
            HTTP_AUTHORIZATION="Bearer",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )