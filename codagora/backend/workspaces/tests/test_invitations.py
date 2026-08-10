from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.test import TestCase
from django.utils import timezone

from workspaces.models import (
    WorkspaceInvitation,
    WorkspaceMember,
)
from workspaces.services import (
    accept_workspace_invitation,
    create_workspace,
    create_workspace_invitation,
    hash_invitation_token,
)


User = get_user_model()


class WorkspaceInvitationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="test-password-123",
        )

        self.member = User.objects.create_user(
            email="member@example.com",
            password="test-password-123",
        )

        self.invited_user = User.objects.create_user(
            email="invited@example.com",
            password="test-password-123",
        )

        self.second_user = User.objects.create_user(
            email="second@example.com",
            password="test-password-123",
        )

        self.workspace = create_workspace(
            owner=self.owner,
            name="Codagora Development",
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=WorkspaceMember.Role.MEMBER,
        )

    def test_owner_can_create_invitation(self):
        invitation, token = create_workspace_invitation(
            workspace=self.workspace,
            created_by=self.owner,
        )

        self.assertEqual(
            invitation.token_hash,
            hash_invitation_token(token),
        )

        self.assertNotEqual(
            invitation.token_hash,
            token,
        )

    def test_member_cannot_create_invitation(self):
        with self.assertRaises(PermissionDenied):
            create_workspace_invitation(
                workspace=self.workspace,
                created_by=self.member,
            )

    def test_user_can_accept_invitation(self):
        invitation, token = create_workspace_invitation(
            workspace=self.workspace,
            created_by=self.owner,
            role=WorkspaceInvitation.Role.MEMBER,
        )

        membership = accept_workspace_invitation(
            user=self.invited_user,
            token=token,
        )

        self.assertEqual(
            membership.workspace,
            self.workspace,
        )

        self.assertEqual(
            membership.user,
            self.invited_user,
        )

        self.assertEqual(
            membership.role,
            WorkspaceMember.Role.MEMBER,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.use_count,
            1,
        )

        self.assertFalse(
            invitation.is_active,
        )

    def test_single_use_invitation_cannot_be_used_twice(self):
        invitation, token = create_workspace_invitation(
            workspace=self.workspace,
            created_by=self.owner,
            max_uses=1,
        )

        accept_workspace_invitation(
            user=self.invited_user,
            token=token,
        )

        with self.assertRaises(ValidationError):
            accept_workspace_invitation(
                user=self.second_user,
                token=token,
            )

    def test_expired_invitation_is_rejected(self):
        invitation, token = create_workspace_invitation(
            workspace=self.workspace,
            created_by=self.owner,
        )

        invitation.expires_at = (
            timezone.now()
            - timedelta(seconds=1)
        )

        invitation.save(
            update_fields=("expires_at",)
        )

        with self.assertRaises(ValidationError):
            accept_workspace_invitation(
                user=self.invited_user,
                token=token,
            )