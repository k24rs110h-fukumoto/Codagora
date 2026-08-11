from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from chat.models import Message
from chat.services import (
    create_message,
    create_text_channel,
)
from workspaces.models import WorkspaceMember
from workspaces.services import create_workspace


User = get_user_model()


class MessageActionApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="test-password-123",
            display_name="Owner",
        )

        self.member = User.objects.create_user(
            email="member@example.com",
            password="test-password-123",
            display_name="Member",
        )

        self.other_member = User.objects.create_user(
            email="other@example.com",
            password="test-password-123",
            display_name="Other Member",
        )

        self.workspace = create_workspace(
            owner=self.owner,
            name="Codagora Development",
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=WorkspaceMember.Role.MEMBER,
            is_active=True,
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_member,
            role=WorkspaceMember.Role.MEMBER,
            is_active=True,
        )

        self.channel = create_text_channel(
            workspace=self.workspace,
            created_by=self.owner,
            name="general",
        )

        self.message = create_message(
            channel=self.channel,
            author=self.member,
            content="最初のメッセージ",
        )

    def get_detail_url(self, message=None):
        target_message = message or self.message

        return reverse(
            "workspaces:chat:message-detail",
            kwargs={
                "workspace_slug": self.workspace.slug,
                "channel_id": self.channel.id,
                "message_id": target_message.id,
            },
        )

    def get_list_url(self):
        return reverse(
            "workspaces:chat:message-list-create",
            kwargs={
                "workspace_slug": self.workspace.slug,
                "channel_id": self.channel.id,
            },
        )

    def test_author_can_edit_own_message(self):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.patch(
            self.get_detail_url(),
            {
                "content": "編集後のメッセージ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.content,
            "編集後のメッセージ",
        )

        self.assertTrue(
            self.message.is_edited,
        )

    def test_member_cannot_edit_another_users_message(
        self,
    ):
        self.client.force_authenticate(
            user=self.other_member,
        )

        response = self.client.patch(
            self.get_detail_url(),
            {
                "content": "勝手に編集",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_author_can_delete_own_message(self):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.delete(
            self.get_detail_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.message.refresh_from_db()

        self.assertIsNotNone(
            self.message.deleted_at,
        )

        self.assertEqual(
            self.message.deleted_by,
            self.member,
        )

        self.assertEqual(
            self.message.content,
            "",
        )

    def test_owner_can_delete_members_message(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.delete(
            self.get_detail_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.deleted_by,
            self.owner,
        )

    def test_member_cannot_delete_another_users_message(
        self,
    ):
        self.client.force_authenticate(
            user=self.other_member,
        )

        response = self.client.delete(
            self.get_detail_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_deleted_message_is_not_returned_in_list(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        self.client.delete(
            self.get_detail_url(),
        )

        response = self.client.get(
            self.get_list_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            0,
        )