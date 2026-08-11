import re

from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import (
    Skill,
    UserFollow,
    UserSkill,
)


User = get_user_model()


class SkillSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = Skill

        fields = (
            "id",
            "name",
        )

        read_only_fields = fields


class UserSkillSerializer(
    serializers.ModelSerializer,
):
    skill = SkillSerializer(
        read_only=True,
    )

    class Meta:
        model = UserSkill

        fields = (
            "id",
            "skill",
            "level",
        )

        read_only_fields = fields


class UserSkillCreateSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=50,
        trim_whitespace=True,
    )

    level = serializers.IntegerField(
        min_value=1,
        max_value=5,
        default=1,
    )


class UserSkillUpdateSerializer(
    serializers.Serializer,
):
    level = serializers.IntegerField(
        min_value=1,
        max_value=5,
    )


class UserSummarySerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = User

        fields = (
            "id",
            "display_name",
            "handle",
            "avatar_url",
        )

        read_only_fields = fields


class CurrentUserSerializer(
    serializers.ModelSerializer,
):
    skills = UserSkillSerializer(
        source="user_skills",
        many=True,
        read_only=True,
    )

    followers_count = (
        serializers.SerializerMethodField()
    )

    following_count = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "display_name",
            "handle",
            "avatar_url",
            "headline",
            "bio",
            "location_name",
            "website_url",
            "github_username",
            "availability",
            "timezone",
            "is_profile_public",
            "skills",
            "followers_count",
            "following_count",
        )

        read_only_fields = (
            "id",
            "email",
            "skills",
            "followers_count",
            "following_count",
        )

    def validate_handle(self, value):
        if value is None:
            return None

        normalized = value.strip().lower()

        if not normalized:
            return None

        if not re.fullmatch(
            r"[a-z0-9_]{3,30}",
            normalized,
        ):
            raise serializers.ValidationError(
                "handleは3〜30文字の英数字または_で入力してください。"
            )

        queryset = User.objects.filter(
            handle__iexact=normalized,
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "このhandleはすでに使用されています。"
            )

        return normalized

    def get_followers_count(self, user):
        return user.follower_relations.count()

    def get_following_count(self, user):
        return user.following_relations.count()


class PublicProfileSerializer(
    serializers.ModelSerializer,
):
    skills = UserSkillSerializer(
        source="user_skills",
        many=True,
        read_only=True,
    )

    followers_count = (
        serializers.SerializerMethodField()
    )

    following_count = (
        serializers.SerializerMethodField()
    )

    is_following = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = User

        fields = (
            "id",
            "display_name",
            "handle",
            "avatar_url",
            "headline",
            "bio",
            "location_name",
            "website_url",
            "github_username",
            "availability",
            "skills",
            "followers_count",
            "following_count",
            "is_following",
        )

        read_only_fields = fields

    def get_followers_count(self, user):
        return user.follower_relations.count()

    def get_following_count(self, user):
        return user.following_relations.count()

    def get_is_following(self, user):
        request = self.context.get("request")

        if (
            not request
            or not request.user.is_authenticated
            or request.user.id == user.id
        ):
            return False

        return UserFollow.objects.filter(
            follower=request.user,
            following=user,
        ).exists()