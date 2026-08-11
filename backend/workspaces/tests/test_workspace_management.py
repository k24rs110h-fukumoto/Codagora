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
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class WorkspaceManagementTests(
    APITestCase,
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email="owner@example.com",
                password=None,
                firebase_uid="owner-uid",
                display_name="Owner",
                handle="owner_user",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.admin = (
            User.objects.create_user(
                email="admin@example.com",
                password=None,
                firebase_uid="admin-uid",
                display_name="Admin",
                handle="admin_user",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.member = (
            User.objects.create_user(
                email="member@example.com",
                password=None,
                firebase_uid="member-uid",
                display_name="Member",
                handle="member_user",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.other = (
            User.objects.create_user(
                email="other@example.com",
                password=None,
                firebase_uid="other-uid",
                display_name="Other",
                handle="other_user",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="Codagora",
            )
        )

        self.admin_membership = (
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=self.admin,
                role=(
                    WorkspaceMember
                    .Role
                    .ADMIN
                ),
            )
        )

        self.member_membership = (
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=self.member,
                role=(
                    WorkspaceMember
                    .Role
                    .MEMBER
                ),
            )
        )

    def authenticate(
        self,
        user,
    ):
        self.client.force_authenticate(
            user=user,
        )

    def test_owner_can_update_workspace(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.patch(
            reverse(
                "workspaces:"
                "workspace-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "name": (
                    "Codagora New"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.workspace.refresh_from_db()

        self.assertEqual(
            self.workspace.name,
            "Codagora New",
        )

    def test_admin_can_update_workspace(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.patch(
            reverse(
                "workspaces:"
                "workspace-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "description": (
                    "Updated"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_member_cannot_update_workspace(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.patch(
            reverse(
                "workspaces:"
                "workspace-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "name": "Invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_only_owner_can_delete_workspace(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.delete(
            reverse(
                "workspaces:"
                "workspace-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_can_promote_member_to_admin(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.patch(
            reverse(
                "workspaces:"
                "workspace-member-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                    "membership_id": (
                        self.member_membership.id
                    ),
                },
            ),
            {
                "role": (
                    WorkspaceMember
                    .Role
                    .ADMIN
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.member_membership.refresh_from_db()

        self.assertEqual(
            self.member_membership.role,
            WorkspaceMember.Role.ADMIN,
        )

    def test_admin_cannot_promote_member_to_admin(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.patch(
            reverse(
                "workspaces:"
                "workspace-member-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                    "membership_id": (
                        self.member_membership.id
                    ),
                },
            ),
            {
                "role": (
                    WorkspaceMember
                    .Role
                    .ADMIN
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_cannot_be_kicked(
        self,
    ):
        owner_membership = (
            WorkspaceMember.objects.get(
                workspace=self.workspace,
                user=self.owner,
            )
        )

        self.authenticate(
            self.admin
        )

        response = self.client.delete(
            reverse(
                "workspaces:"
                "workspace-member-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                    "membership_id": (
                        owner_membership.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_admin_can_remove_member(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.delete(
            reverse(
                "workspaces:"
                "workspace-member-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                    "membership_id": (
                        self.member_membership.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.member_membership.refresh_from_db()

        self.assertFalse(
            self.member_membership.is_active
        )

        self.assertIsNotNone(
            self.member_membership.left_at
        )

    def test_member_can_leave_workspace(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-leave",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.member_membership.refresh_from_db()

        self.assertFalse(
            self.member_membership.is_active
        )

    def test_owner_cannot_leave_without_transfer(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-leave",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_owner_can_transfer_ownership(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            reverse(
                "workspaces:"
                "workspace-transfer-ownership",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            ),
            {
                "membership_id": (
                    self.member_membership.id
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.workspace.refresh_from_db()

        self.member_membership.refresh_from_db()

        owner_membership = (
            WorkspaceMember.objects.get(
                workspace=self.workspace,
                user=self.owner,
            )
        )

        self.assertEqual(
            self.workspace.owner_id,
            self.member.id,
        )

        self.assertEqual(
            self.member_membership.role,
            WorkspaceMember.Role.OWNER,
        )

        self.assertEqual(
            owner_membership.role,
            WorkspaceMember.Role.ADMIN,
        )

    def test_non_member_cannot_access_workspace(
        self,
    ):
        self.authenticate(
            self.other
        )

        response = self.client.get(
            reverse(
                "workspaces:"
                "workspace-detail",
                kwargs={
                    "slug": (
                        self.workspace.slug
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )