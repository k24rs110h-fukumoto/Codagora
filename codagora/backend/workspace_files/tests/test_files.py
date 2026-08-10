import shutil
import tempfile

from django.contrib.auth import (
    get_user_model,
)
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import AccountStatus
from workspace_files.models import (
    WorkspaceFile,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=TEST_MEDIA_ROOT,
)
class WorkspaceFileApiTests(
    APITestCase,
):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(
            TEST_MEDIA_ROOT,
            ignore_errors=True,
        )

    def setUp(self):
        self.owner = User.objects.create_user(
            email="file-owner@example.com",
            password=None,
            firebase_uid="file-owner",
            display_name="Owner",
            handle="file_owner",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.member = User.objects.create_user(
            email="file-member@example.com",
            password=None,
            firebase_uid="file-member",
            display_name="Member",
            handle="file_member",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.other_member = (
            User.objects.create_user(
                email="file-member2@example.com",
                password=None,
                firebase_uid="file-member2",
                display_name="Member2",
                handle="file_member2",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.guest = User.objects.create_user(
            email="file-guest@example.com",
            password=None,
            firebase_uid="file-guest",
            display_name="Guest",
            handle="file_guest",
            account_status=(
                AccountStatus.ACTIVE
            ),
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="Files Workspace",
            )
        )

        for user, role in (
            (
                self.member,
                WorkspaceMember.Role.MEMBER,
            ),
            (
                self.other_member,
                WorkspaceMember.Role.MEMBER,
            ),
            (
                self.guest,
                WorkspaceMember.Role.GUEST,
            ),
        ):
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=user,
                role=role,
            )

    def list_url(self):
        return reverse(
            "workspaces:workspace_files:"
            "file-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def upload(
        self,
        user,
        name="hello.txt",
    ):
        self.client.force_authenticate(
            user=user,
        )

        uploaded_file = (
            SimpleUploadedFile(
                name,
                b"Hello Codagora",
                content_type="text/plain",
            )
        )

        return self.client.post(
            self.list_url(),
            {
                "file": uploaded_file,
            },
            format="multipart",
        )

    def test_member_can_upload_file(
        self,
    ):
        response = self.upload(
            self.member
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        workspace_file = (
            WorkspaceFile.objects.get(
                id=response.data["id"]
            )
        )

        self.assertEqual(
            workspace_file.uploaded_by_id,
            self.member.id,
        )

        self.assertEqual(
            workspace_file.original_name,
            "hello.txt",
        )

        self.assertEqual(
            len(
                workspace_file.sha256
            ),
            64,
        )

    def test_guest_cannot_upload(
        self,
    ):
        response = self.upload(
            self.guest
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guest_can_list_files(
        self,
    ):
        self.upload(
            self.member
        )

        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(
                response.data[
                    "results"
                ]
            ),
            1,
        )

    def test_other_member_cannot_rename_file(
        self,
    ):
        response = self.upload(
            self.member
        )

        file_id = response.data["id"]

        self.client.force_authenticate(
            user=self.other_member,
        )

        response = self.client.patch(
            reverse(
                "workspaces:workspace_files:"
                "file-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "file_id": file_id,
                },
            ),
            {
                "display_name": (
                    "changed.txt"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_owner_can_soft_delete_file(
        self,
    ):
        response = self.upload(
            self.member
        )

        file_id = response.data["id"]

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.delete(
            reverse(
                "workspaces:workspace_files:"
                "file-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "file_id": file_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        workspace_file = (
            WorkspaceFile.objects.get(
                id=file_id
            )
        )

        self.assertIsNotNone(
            workspace_file.deleted_at
        )

        self.assertTrue(
            workspace_file.file.storage.exists(
                workspace_file.file.name
            )
        )

    def test_file_can_be_restored(
        self,
    ):
        response = self.upload(
            self.member
        )

        file_id = response.data["id"]

        workspace_file = (
            WorkspaceFile.objects.get(
                id=file_id
            )
        )

        self.client.force_authenticate(
            user=self.member,
        )

        self.client.delete(
            reverse(
                "workspaces:workspace_files:"
                "file-detail",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "file_id": file_id,
                },
            )
        )

        response = self.client.post(
            reverse(
                "workspaces:workspace_files:"
                "file-restore",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "file_id": file_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        workspace_file.refresh_from_db()

        self.assertIsNone(
            workspace_file.deleted_at
        )

    def test_duplicate_filename_rejected(
        self,
    ):
        first = self.upload(
            self.member
        )

        second = self.upload(
            self.member
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_member_can_download_file(
        self,
    ):
        response = self.upload(
            self.member
        )

        file_id = response.data["id"]

        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.get(
            reverse(
                "workspaces:workspace_files:"
                "file-download",
                kwargs={
                    "workspace_slug": (
                        self.workspace.slug
                    ),
                    "file_id": file_id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "attachment",
            response[
                "Content-Disposition"
            ],
        )