import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ActivityEvent(models.Model):
    class Category(models.TextChoices):
        WORKSPACE = "workspace", "Workspace"
        CHAT = "chat", "Chat"
        TASK = "task", "Task"
        CALENDAR = "calendar", "Calendar"
        FILE = "file", "File"
        MAP = "map", "Map"
        GITHUB = "github", "GitHub"
        ACCOUNT = "account", "Account"
        SYSTEM = "system", "System"

    class Visibility(models.TextChoices):
        ALL_MEMBERS = (
            "all_members",
            "All members",
        )
        CONTRIBUTORS = (
            "contributors",
            "Contributors",
        )
        MANAGERS = (
            "managers",
            "Managers",
        )

    class Source(models.TextChoices):
        INTERNAL = "internal", "Internal"
        GITHUB = "github", "GitHub"
        SYSTEM = "system", "System"

    class EventType(models.TextChoices):
        WORKSPACE_CREATED = (
            "workspace.created",
            "Workspace created",
        )
        WORKSPACE_MEMBER_JOINED = (
            "workspace.member_joined",
            "Workspace member joined",
        )

        CHANNEL_CREATED = (
            "chat.channel_created",
            "Channel created",
        )
        MESSAGE_SENT = (
            "chat.message_sent",
            "Message sent",
        )

        TASK_CREATED = (
            "task.created",
            "Task created",
        )
        TASK_UPDATED = (
            "task.updated",
            "Task updated",
        )
        TASK_COMPLETED = (
            "task.completed",
            "Task completed",
        )

        CALENDAR_CREATED = (
            "calendar.created",
            "Calendar event created",
        )
        CALENDAR_UPDATED = (
            "calendar.updated",
            "Calendar event updated",
        )

        FILE_UPLOADED = (
            "file.uploaded",
            "File uploaded",
        )

        PLACE_CREATED = (
            "map.place_created",
            "Place created",
        )

        GITHUB_REPOSITORY_LINKED = (
            "github.repository_linked",
            "GitHub repository linked",
        )
        GITHUB_SYNCED = (
            "github.synced",
            "GitHub repository synced",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="activity_events",
        null=True,
        blank=True,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_activity_events",
        null=True,
        blank=True,
    )

    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="subject_activity_events",
        null=True,
        blank=True,
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
    )

    event_type = models.CharField(
        max_length=80,
        choices=EventType.choices,
    )

    visibility = models.CharField(
        max_length=30,
        choices=Visibility.choices,
        default=Visibility.ALL_MEMBERS,
    )

    source = models.CharField(
        max_length=30,
        choices=Source.choices,
        default=Source.INTERNAL,
    )

    object_type = models.CharField(
        max_length=80,
        blank=True,
    )

    object_id = models.CharField(
        max_length=128,
        blank=True,
    )

    title = models.CharField(
        max_length=160,
    )

    summary = models.CharField(
        max_length=500,
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

    occurred_at = models.DateTimeField(
        default=timezone.now,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = (
            "-occurred_at",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "occurred_at",
                ),
                name="activity_workspace_time_idx",
            ),
            models.Index(
                fields=(
                    "actor",
                    "occurred_at",
                ),
                name="activity_actor_time_idx",
            ),
            models.Index(
                fields=(
                    "event_type",
                    "occurred_at",
                ),
                name="activity_type_time_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "deduplication_key",
                ),
                condition=Q(
                    deduplication_key__isnull=False,
                ),
                name="activity_unique_dedup_key",
            ),
        ]

    def __str__(self):
        return (
            f"{self.event_type}: "
            f"{self.title}"
        )