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
)


User = get_user_model()


class AccountPermissionTests(
    APITestCase,
):
    def test_provisional_user_cannot_access_workspace_api(
        self,
    ):
        user = (
            User.objects.create_user(
                email=(
                    "provisional@example.com"
                ),
                password=None,
                firebase_uid=(
                    "provisional-uid"
                ),
                account_status=(
                    AccountStatus
                    .PROVISIONAL
                ),
            )
        )

        self.client.force_authenticate(
            user=user,
        )

        response = self.client.get(
            reverse(
                "workspaces:"
                "workspace-list-create"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_verification_required_user_cannot_access_workspace_api(
        self,
    ):
        user = (
            User.objects.create_user(
                email=(
                    "verify@example.com"
                ),
                password=None,
                firebase_uid=(
                    "verify-uid"
                ),
                account_status=(
                    AccountStatus
                    .VERIFICATION_REQUIRED
                ),
            )
        )

        self.client.force_authenticate(
            user=user,
        )

        response = self.client.get(
            reverse(
                "workspaces:"
                "workspace-list-create"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_active_user_can_access_workspace_api(
        self,
    ):
        user = (
            User.objects.create_user(
                email=(
                    "active@example.com"
                ),
                password=None,
                firebase_uid=(
                    "active-uid"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.client.force_authenticate(
            user=user,
        )

        response = self.client.get(
            reverse(
                "workspaces:"
                "workspace-list-create"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )