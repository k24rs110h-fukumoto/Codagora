from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase

from activity.models import (
    ActivityEvent,
)
from activity.services import (
    record_activity_event,
)
from home.services import (
    build_home_payload,
)
from notifications.models import (
    Notification,
)
from notifications.services import (
    create_notification,
)
from tasks.models import (
    TaskStatus,
)
from tasks.services import (
    create_task,
)
from workspaces.models import (
    Workspace,
)


User = get_user_model()


class HomeServiceTests(TestCase):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email=(
                    "home-user@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.other = (
            User.objects.create_user(
                email=(
                    "home-other@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.workspace = (
            Workspace.objects.create(
                name="Home Test",
                slug="home-test",
                owner=self.user,
            )
        )

    def test_empty_home_payload(self):
        payload = (
            build_home_payload(
                user=self.user,
            )
        )

        self.assertIn(
            "continue_working",
            payload,
        )

        self.assertIn(
            "today",
            payload,
        )

        self.assertIn(
            "project_pulse",
            payload,
        )

        self.assertIn(
            "next_move",
            payload,
        )

        self.assertIn(
            "active_workspaces",
            payload,
        )

        self.assertIn(
            "unread_notifications",
            payload,
        )

    def test_workspace_is_in_active_workspaces(
        self,
    ):
        payload = (
            build_home_payload(
                user=self.user,
            )
        )

        workspace_ids = {
            workspace["id"]
            for workspace
            in payload[
                "active_workspaces"
            ]
        }

        self.assertIn(
            str(
                self.workspace.id
            ),
            workspace_ids,
        )

    def test_activity_is_in_project_pulse(
        self,
    ):
        record_activity_event(
            workspace=self.workspace,
            actor=self.user,
            category=(
                ActivityEvent
                .Category
                .WORKSPACE
            ),
            event_type=(
                ActivityEvent
                .EventType
                .WORKSPACE_CREATED
            ),
            title=(
                "Workspace created"
            ),
        )

        payload = (
            build_home_payload(
                user=self.user,
            )
        )

        self.assertEqual(
            len(
                payload[
                    "project_pulse"
                ]
            ),
            1,
        )

    def test_notification_count(
        self,
    ):
        create_notification(
            recipient=self.user,
            actor=self.other,
            workspace=self.workspace,
            notification_type=(
                Notification.Type.SYSTEM
            ),
            category=(
                Notification.Category.SYSTEM
            ),
            title="Test notification",
        )

        payload = (
            build_home_payload(
                user=self.user,
            )
        )

        self.assertEqual(
            payload[
                "unread_notifications"
            ],
            1,
        )

    def test_open_task_affects_workspace(
        self,
    ):
        create_task(
            workspace=self.workspace,
            actor=self.user,
            title="Build Home API",
            status=TaskStatus.TODO,
        )

        payload = (
            build_home_payload(
                user=self.user,
            )
        )

        workspace = (
            payload[
                "active_workspaces"
            ][0]
        )

        self.assertEqual(
            workspace[
                "metrics"
            ][
                "open_tasks"
            ],
            1,
        )