import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class ExploreProject(models.Model):
    class Status(models.TextChoices):
        IDEA = "idea", "Idea"
        BUILDING = "building", "Building"
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "Maintenance"
        COMPLETED = "completed", "Completed"

    class RecruitmentStatus(models.TextChoices):
        CLOSED = "closed", "Closed"
        OPEN = "open", "Open"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="explore_projects",
    )

    workspace = models.OneToOneField(
        "workspaces.Workspace",
        on_delete=models.SET_NULL,
        related_name="explore_project",
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=120,
    )

    summary = models.CharField(
        max_length=300,
    )

    description = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.BUILDING,
    )

    recruitment_status = models.CharField(
        max_length=20,
        choices=RecruitmentStatus.choices,
        default=RecruitmentStatus.CLOSED,
    )

    tags = models.JSONField(
        default=list,
        blank=True,
    )

    tech_stack = models.JSONField(
        default=list,
        blank=True,
    )

    wanted_roles = models.JSONField(
        default=list,
        blank=True,
    )

    repository_url = models.URLField(
        blank=True,
    )

    website_url = models.URLField(
        blank=True,
    )

    cover_image_url = models.URLField(
        blank=True,
    )

    is_published = models.BooleanField(
        default=False,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-published_at",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "is_published",
                    "published_at",
                ),
                name="explore_project_pub_idx",
            ),
            models.Index(
                fields=(
                    "recruitment_status",
                    "published_at",
                ),
                name="explore_project_recruit_idx",
            ),
        ]

    def __str__(self):
        return self.title


class CommunityPost(models.Model):
    class Kind(models.TextChoices):
        DISCUSSION = (
            "discussion",
            "Discussion",
        )

        PROJECT_RECRUITMENT = (
            "project_recruitment",
            "Project recruitment",
        )

        SHOWCASE = (
            "showcase",
            "Showcase",
        )

        QUESTION = (
            "question",
            "Question",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )

    project = models.ForeignKey(
        ExploreProject,
        on_delete=models.SET_NULL,
        related_name="community_posts",
        null=True,
        blank=True,
    )

    kind = models.CharField(
        max_length=40,
        choices=Kind.choices,
        default=Kind.DISCUSSION,
    )

    title = models.CharField(
        max_length=160,
    )

    body = models.TextField()

    tags = models.JSONField(
        default=list,
        blank=True,
    )

    is_published = models.BooleanField(
        default=True,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
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
                    "is_published",
                    "created_at",
                ),
                name="community_post_pub_idx",
            ),
            models.Index(
                fields=(
                    "kind",
                    "created_at",
                ),
                name="community_post_kind_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(is_published=False)
                    | Q(deleted_at__isnull=True)
                ),
                name="community_published_not_deleted",
            ),
        ]

    def __str__(self):
        return self.title


class ExploreEvent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="explore_events",
    )

    title = models.CharField(
        max_length=160,
    )

    summary = models.CharField(
        max_length=300,
    )

    description = models.TextField(
        blank=True,
    )

    starts_at = models.DateTimeField()

    ends_at = models.DateTimeField()

    location_name = models.CharField(
        max_length=160,
        blank=True,
    )

    online_url = models.URLField(
        blank=True,
    )

    tags = models.JSONField(
        default=list,
        blank=True,
    )

    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_published = models.BooleanField(
        default=False,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "starts_at",
            "created_at",
        )

        indexes = [
            models.Index(
                fields=(
                    "is_published",
                    "starts_at",
                ),
                name="explore_event_pub_idx",
            ),
        ]

    def __str__(self):
        return self.title