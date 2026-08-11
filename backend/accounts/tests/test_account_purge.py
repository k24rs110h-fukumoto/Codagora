from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.core.management import (
    call_command,
)
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    AccountStatus,
)


User = get_user_model()


class AccountPurgeTests(
    TestCase,
):
    @patch(
        "accounts.management.commands."
        "purge_deleted_accounts."
        "get_firebase_app"
    )
    @patch(
        "accounts.management.commands."
        "purge_deleted_accounts."
        "auth.delete_user"
    )
    def test_due_account_is_deleted(
        self,
        mock_delete_user,
        mock_get_firebase_app,
    ):
        firebase_app = object()

        mock_get_firebase_app.return_value = (
            firebase_app
        )

        user = (
            User.objects.create_user(
                email=(
                    "delete@example.com"
                ),
                password=None,
                firebase_uid=(
                    "delete-firebase-uid"
                ),
                account_status=(
                    AccountStatus
                    .DELETION_PENDING
                ),
                deletion_requested_at=(
                    timezone.now()
                    - timedelta(days=8)
                ),
                deletion_scheduled_for=(
                    timezone.now()
                    - timedelta(days=1)
                ),
            )
        )

        user_id = user.id

        call_command(
            "purge_deleted_accounts"
        )

        self.assertFalse(
            User.objects.filter(
                id=user_id,
            ).exists()
        )

        mock_delete_user.assert_called_once_with(
            "delete-firebase-uid",
            app=firebase_app,
        )

    @patch(
        "accounts.management.commands."
        "purge_deleted_accounts."
        "get_firebase_app"
    )
    @patch(
        "accounts.management.commands."
        "purge_deleted_accounts."
        "auth.delete_user"
    )
    def test_future_account_is_not_deleted(
        self,
        mock_delete_user,
        mock_get_firebase_app,
    ):
        mock_get_firebase_app.return_value = (
            object()
        )

        user = (
            User.objects.create_user(
                email=(
                    "future@example.com"
                ),
                password=None,
                firebase_uid=(
                    "future-firebase-uid"
                ),
                account_status=(
                    AccountStatus
                    .DELETION_PENDING
                ),
                deletion_requested_at=(
                    timezone.now()
                ),
                deletion_scheduled_for=(
                    timezone.now()
                    + timedelta(days=7)
                ),
            )
        )

        call_command(
            "purge_deleted_accounts"
        )

        self.assertTrue(
            User.objects.filter(
                id=user.id,
            ).exists()
        )

        mock_delete_user.assert_not_called()