import uuid

from django.conf import settings
from django.db import models


class RecurrenceFrequency(models.TextChoices):
    NONE = "none", "None"
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"


class ParticipantResponse(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    TENTATIVE = "tentative", "Tentative"
    DECLINED = "declined", "Declined"


class CalendarEvent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )

    title = models.CharField(
        max_length=160,
    )

    description = models.TextField(
        blank=True,
    )

    location_name = models.CharField(
        max_length=255,
        blank=True,
    )

    timezone = models.CharField(
        max_length=64,
        default="Asia/Tokyo",
    )

    is_all_day = models.BooleanField(
        default=False,
    )

    starts_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    ends_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    recurrence_frequency = models.CharField(
        max_length=20,
        choices=RecurrenceFrequency.choices,
        default=RecurrenceFrequency.NONE,
    )

    recurrence_interval = models.PositiveSmallIntegerField(
        default=1,
    )

    recurrence_weekdays = models.JSONField(
        default=list,
        blank=True,
    )

    recurrence_until = models.DateField(
        null=True,
        blank=True,
    )

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CalendarEventParticipant",
        through_fields=(
            "event",
            "user",
        ),
        related_name="calendar_events",
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_calendar_events",
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
        related_name="deleted_calendar_events",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-updated_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "workspace",
                    "deleted_at",
                ),
                name="calendar_ws_deleted_idx",
            ),
            models.Index(
                fields=(
                    "starts_at",
                ),
                name="calendar_starts_idx",
            ),
            models.Index(
                fields=(
                    "start_date",
                ),
                name="calendar_start_date_idx",
            ),
            models.Index(
                fields=(
                    "recurrence_until",
                ),
                name="calendar_repeat_until_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    recurrence_interval__gte=1,
                ),
                name="calendar_repeat_interval_gte_1",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        is_all_day=True,
                        start_date__isnull=False,
                        end_date__isnull=False,
                        starts_at__isnull=True,
                        ends_at__isnull=True,
                    )
                    | models.Q(
                        is_all_day=False,
                        start_date__isnull=True,
                        end_date__isnull=True,
                        starts_at__isnull=False,
                        ends_at__isnull=False,
                    )
                ),
                name="calendar_event_schedule_shape",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        is_all_day=True,
                        end_date__gte=models.F(
                            "start_date"
                        ),
                    )
                    | models.Q(
                        is_all_day=False,
                        ends_at__gt=models.F(
                            "starts_at"
                        ),
                    )
                ),
                name="calendar_event_valid_period",
            ),
        ]

    def __str__(self):
        return self.title


class CalendarEventParticipant(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.CASCADE,
        related_name="event_participants",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_participations",
    )

    response = models.CharField(
        max_length=20,
        choices=ParticipantResponse.choices,
        default=ParticipantResponse.PENDING,
    )

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_calendar_participants",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "event",
                    "user",
                ),
                name="unique_calendar_event_participant",
            ),
        ]

        indexes = [
            models.Index(
                fields=(
                    "user",
                    "response",
                ),
                name="calendar_participant_user_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.event.title} - "
            f"{self.user}"
        )