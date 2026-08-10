from rest_framework import serializers

from .models import ActivityEvent


class ActivityEventSerializer(
    serializers.ModelSerializer
):
    actor = (
        serializers.SerializerMethodField()
    )

    subject_user = (
        serializers.SerializerMethodField()
    )

    workspace = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = ActivityEvent

        fields = (
            "id",
            "workspace",
            "actor",
            "subject_user",
            "category",
            "event_type",
            "visibility",
            "source",
            "object_type",
            "object_id",
            "title",
            "summary",
            "metadata",
            "occurred_at",
            "created_at",
        )

    def get_actor(
        self,
        obj,
    ):
        return self._user_summary(
            obj.actor
        )

    def get_subject_user(
        self,
        obj,
    ):
        return self._user_summary(
            obj.subject_user
        )

    def get_workspace(
        self,
        obj,
    ):
        if obj.workspace is None:
            return None

        return {
            "id": str(
                obj.workspace.id
            ),
            "slug": (
                obj.workspace.slug
            ),
            "name": (
                obj.workspace.name
            ),
        }

    def _user_summary(
        self,
        user,
    ):
        if user is None:
            return None

        return {
            "id": str(
                user.id
            ),
            "display_name": (
                user.display_name
            ),
            "handle": (
                user.handle
            ),
            "avatar_url": (
                user.avatar_url
            ),
        }


class ActivityOverviewSerializer(
    serializers.Serializer
):
    summary = serializers.DictField()

    skills = serializers.ListField(
        child=(
            serializers.DictField()
        )
    )

    contributions = (
        serializers.ListField(
            child=(
                serializers.DictField()
            )
        )
    )

    portfolio = (
        serializers.DictField()
    )

    career_signals = (
        serializers.ListField(
            child=(
                serializers.DictField()
            )
        )
    )

    ai_insight = (
        serializers.DictField()
    )

    recent_activity = (
        ActivityEventSerializer(
            many=True,
        )
    )

    generated_at = (
        serializers.DateTimeField()
    )