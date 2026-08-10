from types import SimpleNamespace
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase

from activity.models import ActivityEvent
from activity.recorders import (
    record_github_repository_linked,
    record_task_created,
)
from activity.services import record_activity_event
from workspaces.models import Workspace


User = get_user_model()


class ActivityRecorderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="activity-owner@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Activity Test",
            slug="activity-test",
            owner=self.user,
        )

    def test_sensitive_metadata_is_removed(self):
        event = record_activity_event(
            workspace=self.workspace,
            actor=self.user,
            category=ActivityEvent.Category.SYSTEM,
            event_type=(
                ActivityEvent.EventType.WORKSPACE_CREATED
            ),
            title="Security test",
            metadata={
                "safe": "visible",
                "access_token": "secret",
                "refresh_token": "secret",
                "password": "secret",
                "nested": {
                    "private_key": "secret",
                    "normal": "visible",
                },
            },
        )

        self.assertEqual(
            event.metadata["safe"],
            "visible",
        )

        self.assertNotIn(
            "access_token",
            event.metadata,
        )

        self.assertNotIn(
            "refresh_token",
            event.metadata,
        )

        self.assertNotIn(
            "password",
            event.metadata,
        )

        self.assertNotIn(
            "private_key",
            event.metadata["nested"],
        )

        self.assertEqual(
            event.metadata["nested"]["normal"],
            "visible",
        )

    def test_task_created_activity(self):
        task = SimpleNamespace(
            id=uuid4(),
            title="Build Activity",
            status="todo",
            priority="medium",
        )

        event = record_task_created(
            workspace=self.workspace,
            actor=self.user,
            task=task,
        )

        self.assertEqual(
            event.workspace,
            self.workspace,
        )

        self.assertEqual(
            event.actor,
            self.user,
        )

        self.assertEqual(
            event.category,
            ActivityEvent.Category.TASK,
        )

        self.assertEqual(
            event.event_type,
            ActivityEvent.EventType.TASK_CREATED,
        )

        self.assertEqual(
            event.object_type,
            "task",
        )

        self.assertEqual(
            event.object_id,
            str(task.id),
        )

        self.assertEqual(
            event.metadata["task_title"],
            "Build Activity",
        )

    def test_deduplication_key_prevents_duplicate_event(self):
        kwargs = {
            "workspace": self.workspace,
            "actor": self.user,
            "category": ActivityEvent.Category.GITHUB,
            "event_type": (
                ActivityEvent.EventType
                .GITHUB_REPOSITORY_LINKED
            ),
            "title": "GitHub repository linked",
            "deduplication_key": (
                "github.repository_linked:test"
            ),
        }

        first = record_activity_event(
            **kwargs
        )

        second = record_activity_event(
            **kwargs
        )

        self.assertEqual(
            first.id,
            second.id,
        )

        self.assertEqual(
            ActivityEvent.objects.filter(
                deduplication_key=(
                    "github.repository_linked:test"
                )
            ).count(),
            1,
        )

    def test_github_repository_activity(self):
        repository = SimpleNamespace(
            github_repository_id=1328132394,
            full_name=(
                "k24rs110h-fukumoto/Codagora"
            ),
            is_primary=True,
        )

        event = record_github_repository_linked(
            workspace=self.workspace,
            actor=self.user,
            linked_repository=repository,
        )

        self.assertEqual(
            event.category,
            ActivityEvent.Category.GITHUB,
        )

        self.assertEqual(
            event.source,
            ActivityEvent.Source.GITHUB,
        )

        self.assertEqual(
            event.object_id,
            "1328132394",
        )

        self.assertEqual(
            event.metadata["repository"],
            "k24rs110h-fukumoto/Codagora",
        )