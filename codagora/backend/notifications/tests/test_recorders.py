from types import SimpleNamespace
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.models import Notification
from notifications.recorders import (
    notify_calendar_invited,
    notify_file_uploaded,
    notify_github_repository_linked,
    notify_message_reply,
    notify_task_assigned,
    notify_workspace_member_joined,
)
from workspaces.models import Workspace, WorkspaceMember


User = get_user_model()


class NotificationRecorderTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="notify-owner@example.com",
            password="TestPassword123!",
        )
        self.admin = User.objects.create_user(
            email="notify-admin@example.com",
            password="TestPassword123!",
        )
        self.member = User.objects.create_user(
            email="notify-member@example.com",
            password="TestPassword123!",
        )
        self.other = User.objects.create_user(
            email="notify-other@example.com",
            password="TestPassword123!",
        )

        self.workspace = Workspace.objects.create(
            name="Notification Recorder Workspace",
            slug="notification-recorder-workspace",
            owner=self.owner,
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.admin,
            role=WorkspaceMember.Role.ADMIN,
            is_active=True,
        )
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=WorkspaceMember.Role.MEMBER,
            is_active=True,
        )

    def test_workspace_join_notifies_managers(self):
        notify_workspace_member_joined(
            workspace=self.workspace,
            actor=self.other,
            member_user=self.other,
            role=WorkspaceMember.Role.MEMBER,
        )

        recipients = set(
            Notification.objects.values_list(
                "recipient_id",
                flat=True,
            )
        )

        self.assertEqual(
            recipients,
            {
                self.owner.id,
                self.admin.id,
            },
        )

    def test_message_reply_notifies_original_author(self):
        reply_to = SimpleNamespace(
            id=uuid4(),
            author=self.member,
            author_id=self.member.id,
        )
        message = SimpleNamespace(
            id=uuid4(),
        )
        channel = SimpleNamespace(
            id=uuid4(),
            name="general",
        )

        notification = notify_message_reply(
            workspace=self.workspace,
            actor=self.owner,
            message=message,
            reply_to=reply_to,
            channel=channel,
        )

        self.assertIsNotNone(notification)
        self.assertEqual(
            notification.recipient,
            self.member,
        )
        self.assertEqual(
            notification.notification_type,
            Notification.Type.MESSAGE_REPLY,
        )

    def test_task_assignment_skips_actor_self_notification(self):
        task = SimpleNamespace(
            id=uuid4(),
            title="Build notifications",
            status="todo",
            priority="medium",
        )

        notify_task_assigned(
            workspace=self.workspace,
            actor=self.owner,
            task=task,
            recipients=[
                self.owner,
                self.member,
            ],
        )

        notifications = Notification.objects.all()

        self.assertEqual(
            notifications.count(),
            1,
        )
        self.assertEqual(
            notifications.first().recipient,
            self.member,
        )

    def test_calendar_invitation_notifies_participants(self):
        event = SimpleNamespace(
            id=uuid4(),
            title="Sprint planning",
            is_all_day=False,
        )

        notify_calendar_invited(
            workspace=self.workspace,
            actor=self.owner,
            event=event,
            recipients=[
                self.member,
                self.admin,
            ],
        )

        self.assertEqual(
            Notification.objects.filter(
                notification_type=(
                    Notification.Type.CALENDAR_INVITED
                )
            ).count(),
            2,
        )

    def test_file_upload_notifies_workspace_contributors(self):
        workspace_file = SimpleNamespace(
            id=uuid4(),
            display_name="design.pdf",
            size_bytes=1024,
        )

        notify_file_uploaded(
            workspace=self.workspace,
            actor=self.owner,
            workspace_file=workspace_file,
        )

        recipients = set(
            Notification.objects.values_list(
                "recipient_id",
                flat=True,
            )
        )

        self.assertEqual(
            recipients,
            {
                self.admin.id,
                self.member.id,
            },
        )

    def test_github_link_notification_is_deduplicated(self):
        linked_repository = SimpleNamespace(
            github_repository_id=1328132394,
            full_name="k24rs110h-fukumoto/Codagora",
            is_primary=True,
        )

        notify_github_repository_linked(
            workspace=self.workspace,
            actor=self.owner,
            linked_repository=linked_repository,
        )
        notify_github_repository_linked(
            workspace=self.workspace,
            actor=self.owner,
            linked_repository=linked_repository,
        )

        notifications = Notification.objects.filter(
            notification_type=(
                Notification.Type.GITHUB_REPOSITORY_LINKED
            )
        )

        self.assertEqual(
            notifications.count(),
            2,
        )

        recipients = set(
            notifications.values_list(
                "recipient_id",
                flat=True,
            )
        )

        self.assertEqual(
            recipients,
            {
                self.admin.id,
                self.member.id,
            },
        )
