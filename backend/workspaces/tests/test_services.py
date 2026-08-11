from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from workspaces.models import WorkspaceMember
from workspaces.services import create_workspace


User = get_user_model()


class CreateWorkspaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="test-password-123",
            display_name="Owner User",
        )

    def test_create_workspace_creates_owner_membership(self):
        workspace = create_workspace(
            owner=self.user,
            name="Codagora Development",
            description="Codagoraの開発用ワークスペース",
        )

        membership = WorkspaceMember.objects.get(
            workspace=workspace,
            user=self.user,
        )

        self.assertEqual(
            workspace.owner,
            self.user,
        )

        self.assertEqual(
            membership.role,
            WorkspaceMember.Role.OWNER,
        )

        self.assertTrue(
            membership.is_active,
        )

    def test_create_workspace_removes_surrounding_spaces(self):
        workspace = create_workspace(
            owner=self.user,
            name="  Codagora Team  ",
        )

        self.assertEqual(
            workspace.name,
            "Codagora Team",
        )

    def test_create_workspace_rejects_empty_name(self):
        with self.assertRaises(ValidationError):
            create_workspace(
                owner=self.user,
                name="   ",
            )

    def test_create_workspace_generates_different_slugs(self):
        first_workspace = create_workspace(
            owner=self.user,
            name="Development Team",
        )

        second_workspace = create_workspace(
            owner=self.user,
            name="Development Team",
        )

        self.assertNotEqual(
            first_workspace.slug,
            second_workspace.slug,
        )