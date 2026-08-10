from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import WorkspaceMember
from workspaces.services import create_workspace


User = get_user_model()


class WorkspaceApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="test-password-123",
            display_name="Owner",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password-123",
            display_name="Other User",
        )

    def test_authenticated_user_can_create_workspace(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            reverse(
                "workspaces:workspace-list-create"
            ),
            {
                "name": "Codagora Development",
                "description": "開発用ワークスペース",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["name"],
            "Codagora Development",
        )

        self.assertEqual(
            response.data["current_user_role"],
            WorkspaceMember.Role.OWNER,
        )

        self.assertTrue(
            WorkspaceMember.objects.filter(
                workspace__slug=response.data["slug"],
                user=self.owner,
                role=WorkspaceMember.Role.OWNER,
            ).exists()
        )

    def test_user_only_sees_joined_workspaces(self):
        own_workspace = create_workspace(
            owner=self.owner,
            name="Owner Workspace",
        )

        create_workspace(
            owner=self.other_user,
            name="Other Workspace",
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.get(
            reverse(
                "workspaces:workspace-list-create"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_slugs = [
            workspace["slug"]
            for workspace in response.data
        ]

        self.assertIn(
            own_workspace.slug,
            returned_slugs,
        )

        self.assertEqual(
            len(returned_slugs),
            1,
        )

    def test_non_member_cannot_access_workspace_detail(self):
        workspace = create_workspace(
            owner=self.other_user,
            name="Private Workspace",
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.get(
            reverse(
                "workspaces:workspace-detail",
                kwargs={
                    "slug": workspace.slug,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_user_cannot_list_workspaces(self):
        response = self.client.get(
            reverse(
                "workspaces:workspace-list-create"
            )
        )

        self.assertIn(
            response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )