from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse

from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import AccountStatus
from workspace_files.models import (
    WorkspaceFolder,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class WorkspaceFolderApiTests(
    APITestCase,
):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="folder-owner@example.com",
            password=None,
            firebase_uid="folder-owner",
            display_name="Owner",
            handle="folder_owner",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.member = User.objects.create_user(
            email="folder-member@example.com",
            password=None,
            firebase_uid="folder-member",
            display_name="Member",
            handle="folder_member",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.guest = User.objects.create_user(
            email="folder-guest@example.com",
            password=None,
            firebase_uid="folder-guest",
            display_name="Guest",
            handle="folder_guest",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="Folder Workspace",
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember.Role.MEMBER
            ),
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.guest,
            role=(
                WorkspaceMember.Role.GUEST
            ),
        )

    def list_url(self):
        return reverse(
            "workspaces:workspace_files:"
            "folder-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def test_member_can_create_folder(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "name": "Documents",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            WorkspaceFolder.objects.filter(
                workspace=self.workspace,
                name="Documents",
            ).exists()
        )

    def test_guest_cannot_create_folder(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.post(
            self.list_url(),
            {
                "name": "Invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_nested_folder_can_be_created(
        self,
    ):
        parent = (
            WorkspaceFolder.objects.create(
                workspace=self.workspace,
                name="Projects",
                created_by=self.member,
            )
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "name": "Codagora",
                "parent_id": (
                    str(parent.id)
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        child = (
            WorkspaceFolder.objects.get(
                id=response.data["id"]
            )
        )

        self.assertEqual(
            child.parent_id,
            parent.id,
        )

    def test_folder_cannot_move_into_descendant(
        self,
    ):
        parent = (
            WorkspaceFolder.objects.create(
                workspace=self.workspace,
                name="Parent",
                created_by=self.member,
            )
        )

        child = (
            WorkspaceFolder.objects.create(
                workspace=self.workspace,
                name="Child",
                parent=parent,
                created_by=self.member,
            )
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.patch(
            reverse(
                "workspaces:workspace_files:"
                "folder-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "folder_id": (
                        parent.id
                    ),
                },
            ),
            {
                "parent_id": (
                    str(child.id)
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_non_empty_folder_cannot_be_deleted(
        self,
    ):
        parent = (
            WorkspaceFolder.objects.create(
                workspace=self.workspace,
                name="Parent",
                created_by=self.member,
            )
        )

        WorkspaceFolder.objects.create(
            workspace=self.workspace,
            name="Child",
            parent=parent,
            created_by=self.member,
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.delete(
            reverse(
                "workspaces:workspace_files:"
                "folder-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "folder_id": (
                        parent.id
                    ),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_empty_folder_can_be_deleted_and_restored(
        self,
    ):
        folder = (
            WorkspaceFolder.objects.create(
                workspace=self.workspace,
                name="Temporary",
                created_by=self.member,
            )
        )

        self.client.force_authenticate(
            user=self.member,
        )

        delete_response = (
            self.client.delete(
                reverse(
                    "workspaces:workspace_files:"
                    "folder-detail",
                    kwargs={
                        "workspace_slug": (
                            self.workspace.slug
                        ),
                        "folder_id": (
                            folder.id
                        ),
                    },
                )
            )
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        restore_response = (
            self.client.post(
                reverse(
                    "workspaces:workspace_files:"
                    "folder-restore",
                    kwargs={
                        "workspace_slug": (
                            self.workspace.slug
                        ),
                        "folder_id": (
                            folder.id
                        ),
                    },
                )
            )
        )

        self.assertEqual(
            restore_response.status_code,
            status.HTTP_200_OK,
        )

        folder.refresh_from_db()

        self.assertIsNone(
            folder.deleted_at
        )