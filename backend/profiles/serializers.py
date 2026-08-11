from rest_framework import serializers

from .models import DeveloperProfile


class ProfileUserSerializer(
    serializers.Serializer
):
    id = serializers.UUIDField()

    display_name = serializers.CharField(
        allow_blank=True,
    )

    handle = serializers.CharField(
        allow_blank=True,
    )

    avatar_url = serializers.CharField(
        allow_blank=True,
    )


class DeveloperProfileSerializer(
    serializers.ModelSerializer
):
    user = serializers.SerializerMethodField()

    class Meta:
        model = DeveloperProfile

        fields = (
            "id",
            "user",
            "headline",
            "bio",
            "skills",
            "interests",
            "looking_for",
            "availability",
            "location_label",
            "website_url",
            "portfolio_url",
            "github_url",
            "is_public",
            "show_projects",
            "show_activity",
            "created_at",
            "updated_at",
        )

    def get_user(
        self,
        obj,
    ):
        return {
            "id": str(
                obj.user.id
            ),
            "display_name": (
                obj.user.display_name
            ),
            "handle": (
                obj.user.handle
            ),
            "avatar_url": (
                obj.user.avatar_url
            ),
        }


class PublicDeveloperProfileSerializer(
    serializers.ModelSerializer
):
    user = serializers.SerializerMethodField()

    class Meta:
        model = DeveloperProfile

        fields = (
            "id",
            "user",
            "headline",
            "bio",
            "skills",
            "interests",
            "looking_for",
            "availability",
            "location_label",
            "website_url",
            "portfolio_url",
            "github_url",
            "show_projects",
            "show_activity",
            "updated_at",
        )

    def get_user(
        self,
        obj,
    ):
        return {
            "id": str(
                obj.user.id
            ),
            "display_name": (
                obj.user.display_name
            ),
            "handle": (
                obj.user.handle
            ),
            "avatar_url": (
                obj.user.avatar_url
            ),
        }


class DeveloperProfileWriteSerializer(
    serializers.Serializer
):
    headline = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
    )

    bio = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
    )

    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    interests = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    looking_for = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    availability = serializers.ChoiceField(
        choices=(
            DeveloperProfile
            .Availability
            .choices
        ),
        required=False,
    )

    location_label = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
    )

    website_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    portfolio_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    github_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    is_public = serializers.BooleanField(
        required=False,
    )

    show_projects = serializers.BooleanField(
        required=False,
    )

    show_activity = serializers.BooleanField(
        required=False,
    )