import uuid

from django.conf import settings
from django.db import models


class TaskStatus(models.TextChoices):
    TODO = (
        "todo",
        "Todo",
    )

    IN_PROGRESS = (
        "in_progress",
        "In Progress",
    )

    REVIEW = (
        "review",
        "Review",
    )

    DONE = (
        "done",
        "Done",
    )

    CANCELED = (
        "canceled",
        "Canceled",
    )


class TaskPriority(models.TextChoices):
    LOW = (
        "low",
        "Low",
    )

    MEDIUM = (
        "medium",
        "Medium",
    )

    HIGH = (
        "high",
        "High",
    )

    URGENT = (
        "urgent",
        "Urgent",
    )


class Task(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    title = models.CharField(
        max_length=160,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )

    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
    )

    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TaskAssignee",
        through_fields=(
            "task",
            "user",
        ),
        related_name="assigned_workspace_tasks",
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_workspace_tasks",
    )

    due_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    position = models.PositiveIntegerField(
        default=0,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_workspace_tasks",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "status",
            "position",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "status",
                    "position",
                ),
                name="task_ws_status_pos_idx",
            ),
            models.Index(
                fields=(
                    "workspace",
                    "priority",
                ),
                name="task_ws_priority_idx",
            ),
            models.Index(
                fields=(
                    "due_at",
                ),
                name="task_due_at_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    position__gte=0,
                ),
                name="task_position_gte_0",
            ),
        ]

    def __str__(self):
        return self.title


class TaskAssignee(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="task_assignees",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_task_assignments",
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "task",
                    "user",
                ),
                name="unique_task_assignee",
            ),
        ]

        indexes = [
            models.Index(
                fields=(
                    "user",
                    "task",
                ),
                name="task_assignee_user_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.task.title} - "
            f"{self.user}"
        )


class TaskComment(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_comments",
    )

    content = models.TextField(
        max_length=2000,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_task_comments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "task",
                    "created_at",
                ),
                name="task_comment_task_idx",
            ),
        ]

    def __str__(self):
        return str(self.id)