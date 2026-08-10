from django.contrib.auth import get_user_model
from django.test import TestCase

from activity.models import ActivityEvent
from activity.selectors import (
    get_personal_activity_events,
    get_workspace_activity_events,
)
from activity.services import record_activity_event
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)


User = get_user_model()


class ActivitySelectorTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="activity-owner@example.com",
            password="TestPassword123!",
        )

        self.member = User.objects.create_user(
            email="activity-member@example.com",
            password="TestPassword123!",
        )

        self.guest = User.objects.create_user(
            email="activity-guest@example.com",
            password="TestPassword123!",
        )

        self.outsider = User.objects.create_user(
            email="activity-outsider@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Activity Workspace",
            slug="activity-workspace",
            owner=self.owner,
        )

        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.member,
            defaults={
                "role": WorkspaceMember.Role.MEMBER,
                "is_active": True,
            },
        )

        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.guest,
            defaults={
                "role": WorkspaceMember.Role.GUEST,
                "is_active": True,
            },
        )

        self.public_event = record_activity_event(
            workspace=self.workspace,
            actor=self.owner,
            category=ActivityEvent.Category.WORKSPACE,
            event_type=(
                ActivityEvent.EventType.WORKSPACE_CREATED
            ),
            visibility=(
                ActivityEvent.Visibility.ALL_MEMBERS
            ),
            title="Public activity",
        )

        self.contributor_event = (
            record_activity_event(
                workspace=self.workspace,
                actor=self.owner,
                category=(
                    ActivityEvent.Category.TASK
                ),
                event_type=(
                    ActivityEvent.EventType.TASK_UPDATED
                ),
                visibility=(
                    ActivityEvent.Visibility.CONTRIBUTORS
                ),
                title="Contributor activity",
            )
        )

        self.manager_event = (
            record_activity_event(
                workspace=self.workspace,
                actor=self.owner,
                category=(
                    ActivityEvent.Category.SYSTEM
                ),
                event_type=(
                    ActivityEvent.EventType.WORKSPACE_CREATED
                ),
                visibility=(
                    ActivityEvent.Visibility.MANAGERS
                ),
                title="Manager activity",
            )
        )

    def test_owner_can_see_all_workspace_events(self):
        events = get_workspace_activity_events(
            workspace=self.workspace,
            viewer=self.owner,
        )

        self.assertEqual(
            events.count(),
            3,
        )

    def test_member_cannot_see_manager_event(self):
        events = get_workspace_activity_events(
            workspace=self.workspace,
            viewer=self.member,
        )

        ids = set(
            events.values_list(
                "id",
                flat=True,
            )
        )

        self.assertIn(
            self.public_event.id,
            ids,
        )

        self.assertIn(
            self.contributor_event.id,
            ids,
        )

        self.assertNotIn(
            self.manager_event.id,
            ids,
        )

    def test_guest_only_sees_all_members_event(self):
        events = get_workspace_activity_events(
            workspace=self.workspace,
            viewer=self.guest,
        )

        ids = set(
            events.values_list(
                "id",
                flat=True,
            )
        )

        self.assertIn(
            self.public_event.id,
            ids,
        )

        self.assertNotIn(
            self.contributor_event.id,
            ids,
        )

        self.assertNotIn(
            self.manager_event.id,
            ids,
        )

    def test_outsider_sees_no_workspace_events(self):
        events = get_workspace_activity_events(
            workspace=self.workspace,
            viewer=self.outsider,
        )

        self.assertEqual(
            events.count(),
            0,
        )

    def test_category_filter(self):
        events = get_workspace_activity_events(
            workspace=self.workspace,
            viewer=self.owner,
            category=ActivityEvent.Category.TASK,
        )

        self.assertEqual(
            events.count(),
            1,
        )

        self.assertEqual(
            events.first().category,
            ActivityEvent.Category.TASK,
        )

    def test_personal_activity_contains_actor_events(self):
        events = get_personal_activity_events(
            user=self.owner,
        )

        self.assertGreaterEqual(
            events.count(),
            1,
        )