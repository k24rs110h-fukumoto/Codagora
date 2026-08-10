from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase

from notifications.models import (
    Notification,
)
from notifications.selectors import (
    get_unread_notification_count,
    get_user_notifications,
)
from notifications.services import (
    create_notification,
    create_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    mark_notification_as_unread,
)
from workspaces.models import (
    Workspace,
)


User = get_user_model()


class NotificationServiceTests(
    TestCase
):
    def setUp(self):
        self.owner = User.objects.create_user(
            email=(
                "notification-owner@example.com"
            ),
            password="TestPassword123!",
        )

        self.member = User.objects.create_user(
            email=(
                "notification-member@example.com"
            ),
            password="TestPassword123!",
        )

        self.other = User.objects.create_user(
            email=(
                "notification-other@example.com"
            ),
            password="TestPassword123!",
        )

        self.workspace = (
            Workspace.objects.create(
                name="Notification Workspace",
                slug="notification-workspace",
                owner=self.owner,
            )
        )

    def test_create_notification(self):
        notification = (
            create_notification(
                recipient=self.member,
                actor=self.owner,
                workspace=self.workspace,
                notification_type=(
                    Notification.Type.TASK_ASSIGNED
                ),
                category=(
                    Notification.Category.TASK
                ),
                title="Task assigned",
                body="New task",
                object_type="task",
                object_id="123",
            )
        )

        self.assertIsNotNone(
            notification
        )

        self.assertEqual(
            notification.recipient,
            self.member,
        )

        self.assertEqual(
            notification.actor,
            self.owner,
        )

        self.assertFalse(
            notification.is_read
        )

    def test_actor_is_not_notified_about_self(self):
        notification = (
            create_notification(
                recipient=self.owner,
                actor=self.owner,
                notification_type=(
                    Notification.Type.SYSTEM
                ),
                category=(
                    Notification.Category.SYSTEM
                ),
                title="Self notification",
            )
        )

        self.assertIsNone(
            notification
        )

        self.assertEqual(
            Notification.objects.count(),
            0,
        )

    def test_sensitive_metadata_removed(self):
        notification = (
            create_notification(
                recipient=self.member,
                actor=self.owner,
                notification_type=(
                    Notification.Type.SYSTEM
                ),
                category=(
                    Notification.Category.SYSTEM
                ),
                title="Security",
                metadata={
                    "safe": "hello",
                    "access_token": "secret",
                    "password": "secret",
                    "nested": {
                        "refresh_token": (
                            "secret"
                        ),
                        "safe": "world",
                    },
                },
            )
        )

        self.assertEqual(
            notification.metadata[
                "safe"
            ],
            "hello",
        )

        self.assertNotIn(
            "access_token",
            notification.metadata,
        )

        self.assertNotIn(
            "password",
            notification.metadata,
        )

        self.assertNotIn(
            "refresh_token",
            notification.metadata[
                "nested"
            ],
        )

        self.assertEqual(
            notification.metadata[
                "nested"
            ][
                "safe"
            ],
            "world",
        )

    def test_mark_notification_as_read(self):
        notification = (
            create_notification(
                recipient=self.member,
                actor=self.owner,
                notification_type=(
                    Notification.Type.TASK_ASSIGNED
                ),
                category=(
                    Notification.Category.TASK
                ),
                title="Task assigned",
            )
        )

        updated = (
            mark_notification_as_read(
                notification=notification,
                user=self.member,
            )
        )

        self.assertIsNotNone(
            updated.read_at
        )

        self.assertTrue(
            updated.is_read
        )

    def test_mark_notification_as_unread(self):
        notification = (
            create_notification(
                recipient=self.member,
                actor=self.owner,
                notification_type=(
                    Notification.Type.TASK_ASSIGNED
                ),
                category=(
                    Notification.Category.TASK
                ),
                title="Task assigned",
            )
        )

        notification = (
            mark_notification_as_read(
                notification=notification,
                user=self.member,
            )
        )

        notification = (
            mark_notification_as_unread(
                notification=notification,
                user=self.member,
            )
        )

        self.assertIsNone(
            notification.read_at
        )

    def test_mark_all_as_read(self):
        for number in range(3):
            create_notification(
                recipient=self.member,
                actor=self.owner,
                notification_type=(
                    Notification.Type.SYSTEM
                ),
                category=(
                    Notification.Category.SYSTEM
                ),
                title=f"Notification {number}",
            )

        updated_count = (
            mark_all_notifications_as_read(
                user=self.member,
            )
        )

        self.assertEqual(
            updated_count,
            3,
        )

        self.assertEqual(
            get_unread_notification_count(
                user=self.member,
            ),
            0,
        )

    def test_unread_count(self):
        create_notification(
            recipient=self.member,
            actor=self.owner,
            notification_type=(
                Notification.Type.SYSTEM
            ),
            category=(
                Notification.Category.SYSTEM
            ),
            title="Notification",
        )

        self.assertEqual(
            get_unread_notification_count(
                user=self.member,
            ),
            1,
        )

    def test_user_only_gets_own_notifications(self):
        create_notification(
            recipient=self.member,
            actor=self.owner,
            notification_type=(
                Notification.Type.SYSTEM
            ),
            category=(
                Notification.Category.SYSTEM
            ),
            title="Member",
        )

        create_notification(
            recipient=self.other,
            actor=self.owner,
            notification_type=(
                Notification.Type.SYSTEM
            ),
            category=(
                Notification.Category.SYSTEM
            ),
            title="Other",
        )

        notifications = (
            get_user_notifications(
                user=self.member,
            )
        )

        self.assertEqual(
            notifications.count(),
            1,
        )

        self.assertEqual(
            notifications.first().title,
            "Member",
        )

    def test_bulk_notification_does_not_duplicate_users(self):
        notifications = (
            create_notifications(
                recipients=[
                    self.member,
                    self.member,
                    self.other,
                ],
                actor=self.owner,
                notification_type=(
                    Notification.Type.SYSTEM
                ),
                category=(
                    Notification.Category.SYSTEM
                ),
                title="System",
            )
        )

        self.assertEqual(
            len(notifications),
            2,
        )

    def test_deduplication_key(self):
        first = (
            create_notification(
                recipient=self.member,
                actor=self.owner,
                notification_type=(
                    Notification.Type.TASK_ASSIGNED
                ),
                category=(
                    Notification.Category.TASK
                ),
                title="Task assigned",
                deduplication_key=(
                    "task-assigned:123"
                ),
            )
        )

        second = (
            create_notification(
                recipient=self.member,
                actor=self.owner,
                notification_type=(
                    Notification.Type.TASK_ASSIGNED
                ),
                category=(
                    Notification.Category.TASK
                ),
                title="Task assigned",
                deduplication_key=(
                    "task-assigned:123"
                ),
            )
        )

        self.assertEqual(
            first.id,
            second.id,
        )

        self.assertEqual(
            Notification.objects.count(),
            1,
        )