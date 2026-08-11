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
from chat.models import Channel
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class ChannelManagementTests(
    APITestCase,
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email="chat-owner@example.com",
                password=None,
                firebase_uid=(
                    "chat-owner-uid"
                ),
                display_name=(
                    "Chat Owner"
                ),
                handle=(
                    "chat_owner"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.admin = (
            User.objects.create_user(
                email="chat-admin@example.com",
                password=None,
                firebase_uid=(
                    "chat-admin-uid"
                ),
                display_name=(
                    "Chat Admin"
                ),
                handle=(
                    "chat_admin"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.member = (
            User.objects.create_user(
                email=(
                    "chat-member@example.com"
                ),
                password=None,
                firebase_uid=(
                    "chat-member-uid"
                ),
                display_name=(
                    "Chat Member"
                ),
                handle=(
                    "chat_member"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="Chat Workspace",
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.admin,
            role=(
                WorkspaceMember
                .Role
                .ADMIN
            ),
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember
                .Role
                .MEMBER
            ),
        )

        self.channel1 = (
            Channel.objects.create(
                workspace=self.workspace,
                name="general",
                position=0,
                created_by=self.owner,
            )
        )

        self.channel2 = (
            Channel.objects.create(
                workspace=self.workspace,
                name="development",
                position=1,
                created_by=self.owner,
            )
        )

    def authenticate(
        self,
        user,
    ):
        self.client.force_authenticate(
            user=user,
        )

    def channel_list_url(self):
        return reverse(
            "workspaces:chat:"
            "channel-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def test_owner_can_create_channel(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            self.channel_list_url(),
            {
                "name": "Design",
                "description": (
                    "Design discussion"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["name"],
            "design",
        )

        self.assertEqual(
            response.data[
                "channel_type"
            ],
            "text",
        )

    def test_admin_can_create_channel(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.post(
            self.channel_list_url(),
            {
                "name": "backend",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_member_cannot_create_channel(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.post(
            self.channel_list_url(),
            {
                "name": "invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_edit_channel(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.patch(
            reverse(
                "workspaces:chat:"
                "channel-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "channel_id": (
                        self.channel1.id
                    ),
                },
            ),
            {
                "name": (
                    "general-chat"
                ),
                "description": (
                    "General discussion"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.channel1.refresh_from_db()

        self.assertEqual(
            self.channel1.name,
            "general-chat",
        )

    def test_member_cannot_edit_channel(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.patch(
            reverse(
                "workspaces:chat:"
                "channel-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "channel_id": (
                        self.channel1.id
                    ),
                },
            ),
            {
                "name": "changed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_can_archive_channel(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            reverse(
                "workspaces:chat:"
                "channel-archive",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "channel_id": (
                        self.channel1.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.channel1.refresh_from_db()

        self.assertTrue(
            self.channel1.is_archived
        )

        self.assertIsNotNone(
            self.channel1.archived_at
        )

        self.assertEqual(
            self.channel1.archived_by_id,
            self.owner.id,
        )

    def test_archived_channel_is_hidden_from_normal_list(
        self,
    ):
        self.channel1.is_archived = True

        self.channel1.save(
            update_fields=(
                "is_archived",
            )
        )

        self.authenticate(
            self.member
        )

        response = self.client.get(
            self.channel_list_url()
        )

        ids = {
            item["id"]
            for item
            in response.data
        }

        self.assertNotIn(
            str(self.channel1.id),
            ids,
        )

    def test_member_cannot_view_archived_list(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.get(
            reverse(
                "workspaces:chat:"
                "channel-archived-list",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_view_archived_list(
        self,
    ):
        self.channel1.is_archived = True

        self.channel1.save(
            update_fields=(
                "is_archived",
            )
        )

        self.authenticate(
            self.admin
        )

        response = self.client.get(
            reverse(
                "workspaces:chat:"
                "channel-archived-list",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_owner_can_restore_channel(
        self,
    ):
        self.channel1.is_archived = True

        self.channel1.save(
            update_fields=(
                "is_archived",
            )
        )

        self.authenticate(
            self.owner
        )

        response = self.client.post(
            reverse(
                "workspaces:chat:"
                "channel-restore",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "channel_id": (
                        self.channel1.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.channel1.refresh_from_db()

        self.assertFalse(
            self.channel1.is_archived
        )

    def test_restore_fails_when_active_channel_has_same_name(
        self,
    ):
        self.channel1.is_archived = True

        self.channel1.save(
            update_fields=(
                "is_archived",
            )
        )

        Channel.objects.create(
            workspace=self.workspace,
            name="general",
            position=2,
            created_by=self.owner,
        )

        self.authenticate(
            self.owner
        )

        response = self.client.post(
            reverse(
                "workspaces:chat:"
                "channel-restore",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "channel_id": (
                        self.channel1.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_owner_can_reorder_channels(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            reverse(
                "workspaces:chat:"
                "channel-reorder",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "channel_ids": [
                    str(
                        self.channel2.id
                    ),
                    str(
                        self.channel1.id
                    ),
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.channel1.refresh_from_db()
        self.channel2.refresh_from_db()

        self.assertEqual(
            self.channel2.position,
            0,
        )

        self.assertEqual(
            self.channel1.position,
            1,
        )

    def test_member_cannot_reorder_channels(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.post(
            reverse(
                "workspaces:chat:"
                "channel-reorder",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "channel_ids": [
                    str(
                        self.channel2.id
                    ),
                    str(
                        self.channel1.id
                    ),
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )