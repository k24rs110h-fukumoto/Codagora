from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from chat.models import Channel, Message
from chat.services import create_text_channel
from workspaces.models import WorkspaceMember
from workspaces.services import create_workspace


User = get_user_model()


class MessageApiTests(APITestCase):
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

        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="test-password-123",
            display_name="Outsider",
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

        self.channel = create_text_channel(
            workspace=self.workspace,
            created_by=self.owner,
            name="general",
        )

    def get_message_url(self):
        return reverse(
            "workspaces:chat:message-list-create",
            kwargs={
                "workspace_slug": self.workspace.slug,
                "channel_id": self.channel.id,
            },
        )

    def test_member_can_create_message(self):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.get_message_url(),
            {
                "content": "こんにちは",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["content"],
            "こんにちは",
        )

        self.assertTrue(
            Message.objects.filter(
                channel=self.channel,
                author=self.member,
                content="こんにちは",
            ).exists()
        )

    def test_member_can_view_messages(self):
        Message.objects.create(
            channel=self.channel,
            author=self.owner,
            content="テストメッセージ",
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.get(
            self.get_message_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

    def test_empty_message_is_rejected(self):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.get_message_url(),
            {
                "content": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_outsider_cannot_view_messages(self):
        self.client.force_authenticate(
            user=self.outsider,
        )

        response = self.client.get(
            self.get_message_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_can_reply_to_message(self):
        original_message = Message.objects.create(
            channel=self.channel,
            author=self.owner,
            content="元のメッセージ",
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.get_message_url(),
            {
                "content": "返信です",
                "reply_to_id": str(
                    original_message.id
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["reply_to"]["id"],
            str(original_message.id),
        )