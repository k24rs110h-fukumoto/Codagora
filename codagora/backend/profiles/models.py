import uuid

from django.conf import settings
from django.db import models


class DeveloperProfile(models.Model):
    class Availability(models.TextChoices):
        UNAVAILABLE = (
            "unavailable",
            "Unavailable",
        )

        OPEN_TO_PROJECTS = (
            "open_to_projects",
            "Open to projects",
        )

        OPEN_TO_WORK = (
            "open_to_work",
            "Open to work",
        )

        OPEN_TO_BOTH = (
            "open_to_both",
            "Open to projects and work",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="developer_profile",
    )

    headline = models.CharField(
        max_length=120,
        blank=True,
    )

    bio = models.TextField(
        max_length=1000,
        blank=True,
    )

    skills = models.JSONField(
        default=list,
        blank=True,
    )

    interests = models.JSONField(
        default=list,
        blank=True,
    )

    looking_for = models.JSONField(
        default=list,
        blank=True,
    )

    availability = models.CharField(
        max_length=30,
        choices=Availability.choices,
        default=Availability.UNAVAILABLE,
    )

    location_label = models.CharField(
        max_length=120,
        blank=True,
    )

    website_url = models.URLField(
        blank=True,
    )

    portfolio_url = models.URLField(
        blank=True,
    )

    github_url = models.URLField(
        blank=True,
    )

    is_public = models.BooleanField(
        default=False,
    )

    show_projects = models.BooleanField(
        default=True,
    )

    show_activity = models.BooleanField(
        default=False,
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
                    "is_public",
                    "updated_at",
                ),
                name="profile_public_updated_idx",
            ),
            models.Index(
                fields=(
                    "availability",
                    "updated_at",
                ),
                name="profile_availability_idx",
            ),
        ]

    def __str__(self):
        return (
            self.user.display_name
            or self.user.handle
            or str(self.user_id)
        )