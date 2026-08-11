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
    TaskAssignee,
    TaskStatus,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.services import (
    create_workspace,
)


User = get_user_model()


class TaskApiTests(
    APITestCase,
):
    def setUp(self):
        self.owner = (
            User.objects.create_user(
                email=(
                    "task-owner@example.com"
                ),
                password=None,
                firebase_uid=(
                    "task-owner-uid"
                ),
                display_name=(
                    "Task Owner"
                ),
                handle="task_owner",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.member = (
            User.objects.create_user(
                email=(
                    "task-member@example.com"
                ),
                password=None,
                firebase_uid=(
                    "task-member-uid"
                ),
                display_name=(
                    "Task Member"
                ),
                handle="task_member",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.member2 = (
            User.objects.create_user(
                email=(
                    "task-member2@example.com"
                ),
                password=None,
                firebase_uid=(
                    "task-member2-uid"
                ),
                display_name=(
                    "Task Member 2"
                ),
                handle="task_member2",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.guest = (
            User.objects.create_user(
                email=(
                    "task-guest@example.com"
                ),
                password=None,
                firebase_uid=(
                    "task-guest-uid"
                ),
                display_name=(
                    "Task Guest"
                ),
                handle="task_guest",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.other = (
            User.objects.create_user(
                email=(
                    "task-other@example.com"
                ),
                password=None,
                firebase_uid=(
                    "task-other-uid"
                ),
                display_name=(
                    "Other"
                ),
                handle="task_other",
                account_status=(
                    AccountStatus.ACTIVE
                ),
            )
        )

        self.workspace = (
            create_workspace(
                owner=self.owner,
                name="Task Workspace",
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
            user=self.member2,
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

    def authenticate(
        self,
        user,
    ):
        self.client.force_authenticate(
            user=user,
        )

    def list_url(self):
        return reverse(
            "workspaces:tasks:"
            "task-list-create",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
            },
        )

    def detail_url(
        self,
        task,
    ):
        return reverse(
            "workspaces:tasks:"
            "task-detail",
            kwargs={
                "workspace_slug": (
                    self.workspace.slug
                ),
                "task_id": task.id,
            },
        )

    def create_task(
        self,
        *,
        creator=None,
        assignees=None,
    ):
        if creator is None:
            creator = self.owner

        task = Task.objects.create(
            workspace=self.workspace,
            title="Test Task",
            created_by=creator,
        )

        if assignees:
            for user in assignees:
                TaskAssignee.objects.create(
                    task=task,
                    user=user,
                    assigned_by=creator,
                )

        return task

    def test_member_can_create_task(
        self,
    ):
        self.authenticate(
            self.member
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": (
                    "Implement API"
                ),
                "description": (
                    "Create task API"
                ),
                "priority": "high",
                "assignee_ids": [
                    str(
                        self.member.id
                    ),
                    str(
                        self.member2.id
                    ),
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        task = Task.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            task.created_by_id,
            self.member.id,
        )

        self.assertEqual(
            TaskAssignee.objects
            .filter(
                task=task,
            )
            .count(),
            2,
        )

    def test_guest_cannot_create_task(
        self,
    ):
        self.authenticate(
            self.guest
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": "Invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_guest_can_view_tasks(
        self,
    ):
        self.create_task()

        self.authenticate(
            self.guest
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_non_member_cannot_view_tasks(
        self,
    ):
        self.authenticate(
            self.other
        )

        response = self.client.get(
            self.list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_assign_guest(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            self.list_url(),
            {
                "title": (
                    "Invalid assignment"
                ),
                "assignee_ids": [
                    str(
                        self.guest.id
                    ),
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_assignee_can_change_status(
        self,
    ):
        task = self.create_task(
            assignees=[
                self.member,
            ],
        )

        self.authenticate(
            self.member
        )

        response = self.client.patch(
            self.detail_url(
                task
            ),
            {
                "status": (
                    TaskStatus
                    .IN_PROGRESS
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.status,
            TaskStatus.IN_PROGRESS,
        )

    def test_assignee_cannot_change_title(
        self,
    ):
        task = self.create_task(
            assignees=[
                self.member,
            ],
        )

        self.authenticate(
            self.member
        )

        response = self.client.patch(
            self.detail_url(
                task
            ),
            {
                "title": "Changed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_creator_can_update_task(
        self,
    ):
        task = self.create_task(
            creator=self.member,
        )

        self.authenticate(
            self.member
        )

        response = self.client.patch(
            self.detail_url(
                task
            ),
            {
                "title": "Updated",
                "priority": "urgent",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertEqual(
            task.title,
            "Updated",
        )

        self.assertEqual(
            task.priority,
            "urgent",
        )

    def test_done_sets_completed_at(
        self,
    ):
        task = self.create_task(
            creator=self.member,
        )

        self.authenticate(
            self.member
        )

        response = self.client.patch(
            self.detail_url(
                task
            ),
            {
                "status": "done",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        task.refresh_from_db()

        self.assertIsNotNone(
            task.completed_at
        )

    def test_creator_can_soft_delete_task(
        self,
    ):
        task = self.create_task(
            creator=self.member,
        )

        self.authenticate(
            self.member
        )

        response = self.client.delete(
            self.detail_url(
                task
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        task.refresh_from_db()

        self.assertIsNotNone(
            task.deleted_at
        )

        response = self.client.get(
            self.detail_url(
                task
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_task_filter_by_status(
        self,
    ):
        Task.objects.create(
            workspace=self.workspace,
            title="Todo",
            status="todo",
            created_by=self.owner,
        )

        Task.objects.create(
            workspace=self.workspace,
            title="Done",
            status="done",
            created_by=self.owner,
        )

        self.authenticate(
            self.member
        )

        response = self.client.get(
            self.list_url(),
            {
                "status": "done",
            },
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