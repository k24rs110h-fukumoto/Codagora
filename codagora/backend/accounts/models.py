import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class Availability(models.TextChoices):
    UNAVAILABLE = (
        "unavailable",
        "Unavailable",
    )

    COLLABORATION = (
        "collaboration",
        "Open to collaboration",
    )

    WORK = (
        "work",
        "Open to work",
    )


class AccountStatus(models.TextChoices):
    PROVISIONAL = (
        "provisional",
        "Provisional",
    )

    VERIFICATION_REQUIRED = (
        "verification_required",
        "Verification required",
    )

    ACTIVE = (
        "active",
        "Active",
    )

    RESTRICTED = (
        "restricted",
        "Restricted",
    )

    SUSPENDED = (
        "suspended",
        "Suspended",
    )

    DELETION_PENDING = (
        "deletion_pending",
        "Deletion pending",
    )


class LegalDocumentType(models.TextChoices):
    TERMS = (
        "terms",
        "Terms of Service",
    )

    PRIVACY = (
        "privacy",
        "Privacy Policy",
    )


class User(AbstractUser):
    username = None

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
    )

    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
    )

    email_verified = models.BooleanField(
        default=False,
    )

    phone_verified = models.BooleanField(
        default=False,
    )

    auth_providers = models.JSONField(
        default=list,
        blank=True,
    )

    is_anonymous_account = models.BooleanField(
        default=False,
    )

    account_status = models.CharField(
        max_length=30,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    display_name = models.CharField(
        max_length=100,
        blank=True,
    )

    handle = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    avatar_url = models.URLField(
        blank=True,
    )

    headline = models.CharField(
        max_length=120,
        blank=True,
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
    )

    location_name = models.CharField(
        max_length=120,
        blank=True,
    )

    website_url = models.URLField(
        blank=True,
    )

    github_username = models.CharField(
        max_length=100,
        blank=True,
    )

    availability = models.CharField(
        max_length=30,
        choices=Availability.choices,
        default=Availability.UNAVAILABLE,
    )

    timezone = models.CharField(
        max_length=50,
        default="Asia/Tokyo",
    )

    is_profile_public = models.BooleanField(
        default=True,
    )

    onboarding_completed_at = (
        models.DateTimeField(
            null=True,
            blank=True,
        )
    )

    deletion_requested_at = (
        models.DateTimeField(
            null=True,
            blank=True,
        )
    )

    deletion_scheduled_for = (
        models.DateTimeField(
            null=True,
            blank=True,
        )
    )

    deletion_previous_status = (
        models.CharField(
            max_length=30,
            choices=AccountStatus.choices,
            null=True,
            blank=True,
        )
    )

    last_active_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return (
            self.display_name
            or self.email
            or str(self.id)
        )


class Skill(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = (
            "name",
        )

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_skills",
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="users",
    )

    level = models.PositiveSmallIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "user",
                    "skill",
                ),
                name="unique_user_skill",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    level__gte=1,
                    level__lte=5,
                ),
                name="user_skill_level_1_to_5",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.skill}"
        )


class UserFollow(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )

    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "follower",
                    "following",
                ),
                name="unique_user_follow",
            ),
            models.CheckConstraint(
                condition=~models.Q(
                    follower=models.F(
                        "following"
                    ),
                ),
                name="prevent_self_follow",
            ),
        ]

    def __str__(self):
        return (
            f"{self.follower} -> "
            f"{self.following}"
        )


class LegalDocumentAcceptance(
    models.Model,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="legal_acceptances",
    )

    document_type = models.CharField(
        max_length=20,
        choices=LegalDocumentType.choices,
    )

    version = models.CharField(
        max_length=50,
    )

    accepted_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "user",
                    "document_type",
                    "version",
                ),
                name=(
                    "unique_legal_acceptance"
                ),
            ),
        ]

        ordering = (
            "-accepted_at",
        )

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.document_type} "
            f"{self.version}"
        )