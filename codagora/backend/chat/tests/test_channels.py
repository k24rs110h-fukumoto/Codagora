from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import WorkspaceMember
from workspaces.services import create_workspace


User = get_user_model()


class ChannelApiTests(APITestCase):
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

    def get_channel_list_url(self):
        return reverse(
        "workspaces:chat:channel-list-create",
        kwargs={
            "workspace_slug": self.workspace.slug,
        },
    )
    
    def test_owner_can_create_channel(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            self.get_channel_list_url(),
            {
                "name": "General Chat",
                "description": "全体向けチャンネル",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["name"],
            "general-chat",
        )

        self.assertEqual(
            response.data["channel_type"],
            "text",
        )

    def test_member_cannot_create_channel(self):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.get_channel_list_url(),
            {
                "name": "member-channel",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_member_can_view_channel_list(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        self.client.post(
            self.get_channel_list_url(),
            {
                "name": "general",
            },
            format="json",
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.get(
            self.get_channel_list_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["name"],
            "general",
        )

    def test_outsider_cannot_view_channel_list(self):
        self.client.force_authenticate(
            user=self.outsider,
        )

        response = self.client.get(
            self.get_channel_list_url(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_duplicate_channel_name_is_rejected(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        self.client.post(
            self.get_channel_list_url(),
            {
                "name": "general",
            },
            format="json",
        )

        response = self.client.post(
            self.get_channel_list_url(),
            {
                "name": "general",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )