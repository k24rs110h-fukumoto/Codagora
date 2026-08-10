import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Notification(models.Model):
    class Type(models.TextChoices):
        WORKSPACE_MEMBER_JOINED = (
            "workspace.member_joined",
            "Workspace member joined",
        )

        TASK_ASSIGNED = (
            "task.assigned",
            "Task assigned",
        )

        TASK_UPDATED = (
            "task.updated",
            "Task updated",
        )

        TASK_COMPLETED = (
            "task.completed",
            "Task completed",
        )

        CALENDAR_INVITED = (
            "calendar.invited",
            "Calendar invited",
        )

        CALENDAR_UPDATED = (
            "calendar.updated",
            "Calendar updated",
        )

        MESSAGE_REPLY = (
            "chat.message_reply",
            "Message reply",
        )

        FILE_UPLOADED = (
            "file.uploaded",
            "File uploaded",
        )

        GITHUB_REPOSITORY_LINKED = (
            "github.repository_linked",
            "GitHub repository linked",
        )

        SYSTEM = (
            "system",
            "System",
        )

    class Category(models.TextChoices):
        WORKSPACE = "workspace", "Workspace"
        CHAT = "chat", "Chat"
        TASK = "task", "Task"
        CALENDAR = "calendar", "Calendar"
        FILE = "file", "File"
        GITHUB = "github", "GitHub"
        SYSTEM = "system", "System"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="triggered_notifications",
        null=True,
        blank=True,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    notification_type = models.CharField(
        max_length=80,
        choices=Type.choices,
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
    )

    title = models.CharField(
        max_length=160,
    )

    body = models.CharField(
        max_length=500,
        blank=True,
    )

    object_type = models.CharField(
        max_length=80,
        blank=True,
    )

    object_id = models.CharField(
        max_length=128,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    deduplication_key = models.CharField(
        max_length=191,
        null=True,
        blank=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "recipient",
                    "created_at",
                ),
                name="notify_recipient_time_idx",
            ),
            models.Index(
                fields=(
                    "recipient",
                    "read_at",
                ),
                name="notify_recipient_read_idx",
            ),
            models.Index(
                fields=(
                    "workspace",
                    "created_at",
                ),
                name="notify_workspace_time_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "recipient",
                    "deduplication_key",
                ),
                condition=Q(
                    deduplication_key__isnull=False,
                ),
                name="notify_recipient_dedup_unique",
            ),
        ]

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self):
        return (
            f"{self.recipient_id}: "
            f"{self.notification_type}"
        )