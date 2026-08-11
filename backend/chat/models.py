import uuid

from django.conf import settings
from django.db import models


class Channel(models.Model):
    class ChannelType(models.TextChoices):
        TEXT = "text", "Text"
        VOICE = "voice", "Voice"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="channels",
    )

    name = models.SlugField(
        max_length=80,
        allow_unicode=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    channel_type = models.CharField(
        max_length=20,
        choices=ChannelType.choices,
        default=ChannelType.TEXT,
    )

    position = models.PositiveIntegerField(
        default=0,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    archived_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archived_channels",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_channels",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "position",
            "created_at",
        )

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "workspace",
                    "name",
                ),
                condition=models.Q(
                    is_archived=False,
                ),
                name="unique_active_channel_name_per_workspace",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    position__gte=0,
                ),
                name="channel_position_gte_0",
            ),
        ]

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "is_archived",
                    "position",
                ),
                name="chat_channel_ws_arch_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.workspace.name} / "
            f"{self.name}"
        )


class Message(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )

    content = models.TextField()

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    is_edited = models.BooleanField(
        default=False,
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
        related_name="deleted_messages",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "channel",
                    "created_at",
                ),
                name="chat_msg_channel_idx",
            ),
            models.Index(
                fields=(
                    "author",
                    "created_at",
                ),
                name="chat_msg_author_idx",
            ),
        ]

    def __str__(self):
        return str(self.id)