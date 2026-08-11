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
from tasks.models import (
    Task,
    TaskComment,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class TaskCommentApiTests(
    APITestCase,
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email=(
                    "comment-owner@example.com"
                ),
                password=None,
                firebase_uid=(
                    "comment-owner-uid"
                ),
                display_name="Owner",
                handle=(
                    "comment_owner"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.member = (
            User.objects.create_user(
                email=(
                    "comment-member@example.com"
                ),
                password=None,
                firebase_uid=(
                    "comment-member-uid"
                ),
                display_name="Member",
                handle=(
                    "comment_member"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.guest = (
            User.objects.create_user(
                email=(
                    "comment-guest@example.com"
                ),
                password=None,
                firebase_uid=(
                    "comment-guest-uid"
                ),
                display_name="Guest",
                handle=(
                    "comment_guest"
                ),
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name=(
                    "Comment Workspace"
                ),
            )
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember
                .Role
                .MEMBER
            ),
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.guest,
            role=(
                WorkspaceMember
                .Role
                .GUEST
            ),
        )

        self.task = (
            Task.objects.create(
                workspace=self.workspace,
                title="Task",
                created_by=self.owner,
            )
        )

    def list_url(self):
        return reverse(
            "workspaces:tasks:"
            "task-comment-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
                "task_id": (
                    self.task.id
                ),
            },
        )

    def detail_url(
        self,
        comment,
    ):
        return reverse(
            "workspaces:tasks:"
            "task-comment-detail",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
                "task_id": (
                    self.task.id
                ),
                "comment_id": (
                    comment.id
                ),
            },
        )

    def test_member_can_comment(
        self,
    ):
        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.post(
            self.list_url(),
            {
                "content": (
                    "Working on this."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            TaskComment.objects.count(),
            1,
        )

    def test_guest_cannot_comment(
        self,
    ):
        self.client.force_authenticate(
            user=self.guest,
        )

        response = self.client.post(
            self.list_url(),
            {
                "content": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guest_can_read_comments(
        self,
    ):
        TaskComment.objects.create(
            task=self.task,
            author=self.member,
            content="Comment",
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

    def test_author_can_edit_comment(
        self,
    ):
        comment = (
            TaskComment.objects.create(
                task=self.task,
                author=self.member,
                content="Old",
            )
        )

        self.client.force_authenticate(
            user=self.member,
        )

        response = self.client.patch(
            self.detail_url(
                comment
            ),
            {
                "content": "New",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        comment.refresh_from_db()

        self.assertEqual(
            comment.content,
            "New",
        )

    def test_owner_can_delete_member_comment(
        self,
    ):
        comment = (
            TaskComment.objects.create(
                task=self.task,
                author=self.member,
                content="Delete",
            )
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.delete(
            self.detail_url(
                comment
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        comment.refresh_from_db()

        self.assertIsNotNone(
            comment.deleted_at
        )