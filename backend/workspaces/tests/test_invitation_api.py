from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import (
    WorkspaceInvitation,
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
    create_workspace_invitation,
    hash_invitation_token,
)


User = get_user_model()


class WorkspaceInvitationApiTests(APITestCase):
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

        self.invited_user = User.objects.create_user(
            email="invited@example.com",
            password="test-password-123",
            display_name="Invited User",
        )

        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="test-password-123",
            display_name="Outsider",
        )

        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="test-password-123",
            display_name="Inactive User",
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
            user=self.inactive_user,
            role=WorkspaceMember.Role.MEMBER,
            is_active=False,
        )

    def test_owner_can_create_invitation(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": self.workspace.slug,
                },
            ),
            {
                "role": WorkspaceInvitation.Role.MEMBER,
                "expires_in_days": 7,
                "max_uses": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertIn(
            "token",
            response.data,
        )

        invitation = (
            WorkspaceInvitation.objects.get(
                id=response.data["id"],
            )
        )

        self.assertEqual(
            invitation.token_hash,
            hash_invitation_token(
                response.data["token"]
            ),
        )

        self.assertNotEqual(
            invitation.token_hash,
            response.data["token"],
        )

    def test_member_cannot_create_invitation(self):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": self.workspace.slug,
                },
            ),
            {
                "role": WorkspaceInvitation.Role.MEMBER,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_can_accept_invitation(self):
        invitation, token = (
            create_workspace_invitation(
                workspace=self.workspace,
                created_by=self.owner,
                role=WorkspaceInvitation.Role.MEMBER,
            )
        )

        self.client.force_authenticate(
            user=self.invited_user,
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-accept"
            ),
            {
                "token": token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["workspace"]["slug"],
            self.workspace.slug,
        )

        self.assertEqual(
            response.data["role"],
            WorkspaceMember.Role.MEMBER,
        )

        self.assertTrue(
            WorkspaceMember.objects.filter(
                workspace=self.workspace,
                user=self.invited_user,
                is_active=True,
            ).exists()
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.use_count,
            1,
        )

    def test_member_list_only_contains_active_members(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.get(
            reverse(
                "workspaces:workspace-member-list",
                kwargs={
                    "slug": self.workspace.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_user_ids = {
            str(member["user"]["id"])
            for member in response.data
        }

        self.assertIn(
            str(self.owner.id),
            returned_user_ids,
        )

        self.assertIn(
            str(self.member.id),
            returned_user_ids,
        )

        self.assertNotIn(
            str(self.inactive_user.id),
            returned_user_ids,
        )

    def test_outsider_cannot_view_member_list(self):
        self.client.force_authenticate(
            user=self.outsider,
        )

        response = self.client.get(
            reverse(
                "workspaces:workspace-member-list",
                kwargs={
                    "slug": self.workspace.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_user_cannot_accept_invitation(
        self,
    ):
        invitation, token = (
            create_workspace_invitation(
                workspace=self.workspace,
                created_by=self.owner,
            )
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-accept"
            ),
            {
                "token": token,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.use_count,
            0,
        )