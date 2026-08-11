import tempfile

from django.contrib.auth import (
    get_user_model,
)
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import (
    TestCase,
    override_settings,
)

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from workspace_files.downloads import (
    get_workspace_file_for_download,
    require_workspace_file_viewer,
)
from workspace_files.services import (
    upload_workspace_file,
)


User = get_user_model()


class WorkspaceFileDownloadTests(
    TestCase
):
    def setUp(self):
        self.temp_media = (
            tempfile.TemporaryDirectory()
        )

        self.media_override = (
            override_settings(
                MEDIA_ROOT=(
                    self.temp_media.name
                ),
                WORKSPACE_FILE_MAX_UPLOAD_SIZE_BYTES=(
                    10 * 1024 * 1024
                ),
            )
        )

        self.media_override.enable()

        self.owner = (
            User.objects.create_user(
                email=(
                    "download-owner@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.member = (
            User.objects.create_user(
                email=(
                    "download-member@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.guest = (
            User.objects.create_user(
                email=(
                    "download-guest@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.outsider = (
            User.objects.create_user(
                email=(
                    "download-outsider@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.workspace = (
            Workspace.objects.create(
                name="Download Workspace",
                slug="download-workspace",
                owner=self.owner,
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember.Role.MEMBER
            ),
            is_active=True,
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.guest,
            role=(
                WorkspaceMember.Role.GUEST
            ),
            is_active=True,
        )

        uploaded_file = (
            SimpleUploadedFile(
                "document.txt",
                b"Codagora secure file",
                content_type="text/plain",
            )
        )

        self.workspace_file = (
            upload_workspace_file(
                workspace=self.workspace,
                actor=self.owner,
                uploaded_file=(
                    uploaded_file
                ),
            )
        )

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def test_owner_can_view_file(
        self,
    ):
        role = (
            require_workspace_file_viewer(
                workspace=self.workspace,
                user=self.owner,
            )
        )

        self.assertEqual(
            role,
            WorkspaceMember.Role.OWNER,
        )

    def test_member_can_view_file(
        self,
    ):
        role = (
            require_workspace_file_viewer(
                workspace=self.workspace,
                user=self.member,
            )
        )

        self.assertEqual(
            role,
            WorkspaceMember.Role.MEMBER,
        )

    def test_guest_can_view_file(
        self,
    ):
        role = (
            require_workspace_file_viewer(
                workspace=self.workspace,
                user=self.guest,
            )
        )

        self.assertEqual(
            role,
            WorkspaceMember.Role.GUEST,
        )

    def test_outsider_cannot_view_file(
        self,
    ):
        with self.assertRaises(
            PermissionDenied
        ):
            require_workspace_file_viewer(
                workspace=self.workspace,
                user=self.outsider,
            )

    def test_member_can_get_file_for_download(
        self,
    ):
        workspace_file = (
            get_workspace_file_for_download(
                file_id=(
                    self.workspace_file.id
                ),
                user=self.member,
            )
        )

        self.assertEqual(
            workspace_file.id,
            self.workspace_file.id,
        )

    def test_outsider_cannot_get_file_for_download(
        self,
    ):
        with self.assertRaises(
            PermissionDenied
        ):
            get_workspace_file_for_download(
                file_id=(
                    self.workspace_file.id
                ),
                user=self.outsider,
            )

    def test_deleted_file_cannot_be_downloaded(
        self,
    ):
        self.workspace_file.deleted_at = (
            self.workspace_file.created_at
        )

        self.workspace_file.save(
            update_fields=(
                "deleted_at",
                "updated_at",
            )
        )

        with self.assertRaises(
            ValidationError
        ):
            get_workspace_file_for_download(
                file_id=(
                    self.workspace_file.id
                ),
                user=self.owner,
            )