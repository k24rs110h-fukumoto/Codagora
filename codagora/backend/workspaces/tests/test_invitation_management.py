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
from workspaces.models import (
    WorkspaceInvitation,
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class WorkspaceInvitationManagementTests(
    APITestCase,
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email="owner2@example.com",
                password=None,
                firebase_uid="owner2-uid",
                display_name="Owner",
                handle="owner_two",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.admin = (
            User.objects.create_user(
                email="admin2@example.com",
                password=None,
                firebase_uid="admin2-uid",
                display_name="Admin",
                handle="admin_two",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.joiner = (
            User.objects.create_user(
                email="join@example.com",
                password=None,
                firebase_uid="join-uid",
                display_name="Join",
                handle="join_user",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="Invite Test",
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.admin,
            role=(
                WorkspaceMember.Role.ADMIN
            ),
        )

    def test_owner_can_create_invitation(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "role": "member",
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

        self.assertNotIn(
            "token_hash",
            response.data,
        )

    def test_admin_cannot_create_admin_invitation(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin,
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "role": "admin",
                "expires_in_days": 7,
                "max_uses": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_can_list_invitations(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "role": "member",
            },
            format="json",
        )

        response = self.client.get(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertNotIn(
            "token_hash",
            response.data[0],
        )

    def test_invitation_can_be_revoked(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        create_response = (
            self.client.post(
                reverse(
                    "workspaces:"
                    "workspace-invitation-create",
                    kwargs={
                        "slug": (
                            self.workspace.slug
                        ),
                    },
                ),
                {
                    "role": "member",
                },
                format="json",
            )
        )

        invitation_id = (
            create_response.data["id"]
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-revoke",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                    "invitation_id": (
                        invitation_id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invitation = (
            WorkspaceInvitation.objects.get(
                id=invitation_id,
            )
        )

        self.assertFalse(
            invitation.is_active
        )

        self.assertIsNotNone(
            invitation.revoked_at
        )

    def test_invitation_can_be_reissued(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        original = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "role": "member",
            },
            format="json",
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-reissue",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                    "invitation_id": (
                        original.data["id"]
                    ),
                },
            ),
            {
                "expires_in_days": 14,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertNotEqual(
            response.data["id"],
            original.data["id"],
        )

        self.assertIn(
            "token",
            response.data,
        )

        old_invitation = (
            WorkspaceInvitation.objects.get(
                id=original.data["id"],
            )
        )

        self.assertFalse(
            old_invitation.is_active
        )

    def test_user_can_accept_invitation(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        created = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "role": "member",
            },
            format="json",
        )

        token = created.data["token"]

        self.client.force_authenticate(
            user=self.joiner,
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

        membership = (
            WorkspaceMember.objects.get(
                workspace=self.workspace,
                user=self.joiner,
            )
        )

        self.assertTrue(
            membership.is_active
        )

        self.assertEqual(
            membership.role,
            WorkspaceMember.Role.MEMBER,
        )

    def test_invitation_cannot_be_used_twice_by_same_user(
        self,
    ):
        self.client.force_authenticate(
            user=self.owner,
        )

        created = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-create",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "role": "member",
                "max_uses": 2,
            },
            format="json",
        )

        token = created.data["token"]

        self.client.force_authenticate(
            user=self.joiner,
        )

        first = self.client.post(
            reverse(
                "workspaces:"
                "workspace-invitation-accept"
            ),
            {
                "token": token,
            },
            format="json",
        )

        second = self.client.post(
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
            first.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_400_BAD_REQUEST,
        )