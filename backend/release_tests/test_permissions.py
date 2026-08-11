from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from locations.services import (
    can_manage_place,
    require_location_share_viewer,
)
from scheduling.services import (
    can_manage_event,
)
from tasks.services import (
    create_task,
    create_task_comment,
    delete_task,
    delete_task_comment,
    update_task,
    update_task_comment,
)
from workspace_files.services import (
    can_manage_file,
    can_manage_folder,
)
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)


User = get_user_model()


class ReleasePermissionHardeningTests(
    TestCase
):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="release-owner@example.com",
            password="TestPassword123!",
        )

        self.member = User.objects.create_user(
            email="release-member@example.com",
            password="TestPassword123!",
        )

        self.other_member = (
            User.objects.create_user(
                email=(
                    "release-other@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.workspace = (
            Workspace.objects.create(
                name="Release Workspace",
                slug="release-workspace",
                owner=self.owner,
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
                is_active=True,
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.other_member,
            role=(
                WorkspaceMember
                .Role
                .MEMBER
            ),
            is_active=True,
        )

    def downgrade_member_to_guest(
        self,
    ):
        self.member_membership.role = (
            WorkspaceMember.Role.GUEST
        )

        self.member_membership.save(
            update_fields=(
                "role",
            )
        )

    def test_member_can_manage_own_calendar_before_downgrade(
        self,
    ):
        event = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.assertTrue(
            can_manage_event(
                event=event,
                user=self.member,
            )
        )

    def test_guest_cannot_manage_calendar_created_before_downgrade(
        self,
    ):
        event = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.downgrade_member_to_guest()

        self.assertFalse(
            can_manage_event(
                event=event,
                user=self.member,
            )
        )

    def test_owner_can_manage_calendar(
        self,
    ):
        event = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.assertTrue(
            can_manage_event(
                event=event,
                user=self.owner,
            )
        )

    def test_member_can_manage_own_folder_before_downgrade(
        self,
    ):
        folder = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.assertTrue(
            can_manage_folder(
                folder=folder,
                user=self.member,
            )
        )

    def test_guest_cannot_manage_folder_created_before_downgrade(
        self,
    ):
        folder = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.downgrade_member_to_guest()

        self.assertFalse(
            can_manage_folder(
                folder=folder,
                user=self.member,
            )
        )

    def test_member_can_manage_own_file_before_downgrade(
        self,
    ):
        workspace_file = (
            SimpleNamespace(
                workspace=self.workspace,
                uploaded_by_id=(
                    self.member.id
                ),
            )
        )

        self.assertTrue(
            can_manage_file(
                workspace_file=(
                    workspace_file
                ),
                user=self.member,
            )
        )

    def test_guest_cannot_manage_file_uploaded_before_downgrade(
        self,
    ):
        workspace_file = (
            SimpleNamespace(
                workspace=self.workspace,
                uploaded_by_id=(
                    self.member.id
                ),
            )
        )

        self.downgrade_member_to_guest()

        self.assertFalse(
            can_manage_file(
                workspace_file=(
                    workspace_file
                ),
                user=self.member,
            )
        )

    def test_owner_can_manage_other_users_file(
        self,
    ):
        workspace_file = (
            SimpleNamespace(
                workspace=self.workspace,
                uploaded_by_id=(
                    self.member.id
                ),
            )
        )

        self.assertTrue(
            can_manage_file(
                workspace_file=(
                    workspace_file
                ),
                user=self.owner,
            )
        )

    def test_member_can_manage_own_place_before_downgrade(
        self,
    ):
        place = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.assertTrue(
            can_manage_place(
                place=place,
                user=self.member,
            )
        )

    def test_guest_cannot_manage_place_created_before_downgrade(
        self,
    ):
        place = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.downgrade_member_to_guest()

        self.assertFalse(
            can_manage_place(
                place=place,
                user=self.member,
            )
        )

    def test_guest_cannot_view_live_location_share(
        self,
    ):
        self.downgrade_member_to_guest()

        with self.assertRaises(
            PermissionDenied
        ):
            require_location_share_viewer(
                workspace=self.workspace,
                user=self.member,
            )

    def test_task_creator_cannot_update_after_guest_downgrade(
        self,
    ):
        task = create_task(
            workspace=self.workspace,
            actor=self.member,
            title="Release Test Task",
            assignee_ids=[
                self.member.id,
            ],
        )

        self.downgrade_member_to_guest()

        with self.assertRaises(
            PermissionDenied
        ):
            update_task(
                task=task,
                actor=self.member,
                changes={
                    "title": (
                        "Unauthorized Update"
                    ),
                },
            )

        task.refresh_from_db()

        self.assertEqual(
            task.title,
            "Release Test Task",
        )

    def test_task_creator_cannot_delete_after_guest_downgrade(
        self,
    ):
        task = create_task(
            workspace=self.workspace,
            actor=self.member,
            title="Delete Test Task",
        )

        self.downgrade_member_to_guest()

        with self.assertRaises(
            PermissionDenied
        ):
            delete_task(
                task=task,
                actor=self.member,
            )

        task.refresh_from_db()

        self.assertIsNone(
            task.deleted_at
        )

    def test_task_assignee_cannot_update_after_guest_downgrade(
        self,
    ):
        task = create_task(
            workspace=self.workspace,
            actor=self.owner,
            title="Assigned Task",
            assignee_ids=[
                self.member.id,
            ],
        )

        self.downgrade_member_to_guest()

        with self.assertRaises(
            PermissionDenied
        ):
            update_task(
                task=task,
                actor=self.member,
                changes={
                    "status": "done",
                },
            )

    def test_comment_author_cannot_update_after_guest_downgrade(
        self,
    ):
        task = create_task(
            workspace=self.workspace,
            actor=self.member,
            title="Comment Task",
        )

        comment = (
            create_task_comment(
                task=task,
                actor=self.member,
                content=(
                    "Original comment"
                ),
            )
        )

        self.downgrade_member_to_guest()

        with self.assertRaises(
            PermissionDenied
        ):
            update_task_comment(
                comment=comment,
                actor=self.member,
                content=(
                    "Unauthorized comment"
                ),
            )

        comment.refresh_from_db()

        self.assertEqual(
            comment.content,
            "Original comment",
        )

    def test_comment_author_cannot_delete_after_guest_downgrade(
        self,
    ):
        task = create_task(
            workspace=self.workspace,
            actor=self.member,
            title="Comment Delete Task",
        )

        comment = (
            create_task_comment(
                task=task,
                actor=self.member,
                content="Comment",
            )
        )

        self.downgrade_member_to_guest()

        with self.assertRaises(
            PermissionDenied
        ):
            delete_task_comment(
                comment=comment,
                actor=self.member,
            )

        comment.refresh_from_db()

        self.assertIsNone(
            comment.deleted_at
        )

    def test_owner_still_has_management_permissions(
        self,
    ):
        folder = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        workspace_file = (
            SimpleNamespace(
                workspace=self.workspace,
                uploaded_by_id=(
                    self.member.id
                ),
            )
        )

        place = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        event = SimpleNamespace(
            workspace=self.workspace,
            created_by_id=(
                self.member.id
            ),
        )

        self.assertTrue(
            can_manage_folder(
                folder=folder,
                user=self.owner,
            )
        )

        self.assertTrue(
            can_manage_file(
                workspace_file=(
                    workspace_file
                ),
                user=self.owner,
            )
        )

        self.assertTrue(
            can_manage_place(
                place=place,
                user=self.owner,
            )
        )

        self.assertTrue(
            can_manage_event(
                event=event,
                user=self.owner,
            )
        )