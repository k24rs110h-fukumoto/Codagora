from rest_framework import serializers

from .models import Notification


class NotificationSerializer(
    serializers.ModelSerializer
):
    actor = (
        serializers.SerializerMethodField()
    )

    workspace = (
        serializers.SerializerMethodField()
    )

    is_read = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = Notification

        fields = (
            "id",
            "notification_type",
            "category",
            "title",
            "body",
            "actor",
            "workspace",
            "object_type",
            "object_id",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        )

    def get_actor(
        self,
        obj,
    ):
        if obj.actor is None:
            return None

        return {
            "id": str(
                obj.actor.id
            ),
            "display_name": (
                obj.actor.display_name
            ),
            "handle": (
                obj.actor.handle
            ),
            "avatar_url": (
                obj.actor.avatar_url
            ),
        }

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