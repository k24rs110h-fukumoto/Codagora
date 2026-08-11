from rest_framework import (
    serializers,
)

from accounts.models import User

from .models import (
    Channel,
    Message,
)


class ChatUserSummarySerializer(
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


class ChannelSerializer(
    serializers.ModelSerializer,
):
    created_by = (
        ChatUserSummarySerializer(
            read_only=True,
        )
    )

    archived_by = (
        ChatUserSummarySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = Channel

        fields = (
            "id",
            "name",
            "description",
            "channel_type",
            "position",
            "is_archived",
            "archived_at",
            "archived_by",
            "created_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class ChannelCreateSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=80,
        trim_whitespace=True,
    )

    description = (
        serializers.CharField(
            max_length=255,
            required=False,
            allow_blank=True,
            default="",
            trim_whitespace=True,
        )
    )


class ChannelUpdateSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=80,
        required=False,
        trim_whitespace=True,
    )

    description = (
        serializers.CharField(
            max_length=255,
            required=False,
            allow_blank=True,
            trim_whitespace=True,
        )
    )

    def validate(self, attrs):
        if not attrs:
            raise (
                serializers.ValidationError(
                    "変更する項目を"
                    "指定してください。"
                )
            )

        return attrs


class ChannelReorderSerializer(
    serializers.Serializer,
):
    channel_ids = (
        serializers.ListField(
            child=(
                serializers.UUIDField()
            ),
            allow_empty=False,
        )
    )


class MessageReplySerializer(
    serializers.ModelSerializer,
):
    author = (
        ChatUserSummarySerializer(
            read_only=True,
        )
    )

    content = (
        serializers.SerializerMethodField()
    )

    is_deleted = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Message

        fields = (
            "id",
            "author",
            "content",
            "is_deleted",
            "created_at",
        )

        read_only_fields = fields

    def get_content(
        self,
        obj,
    ):
        if obj.deleted_at:
            return None

        return obj.content

    def get_is_deleted(
        self,
        obj,
    ):
        return (
            obj.deleted_at
            is not None
        )


class MessageSerializer(
    serializers.ModelSerializer,
):
    author = (
        ChatUserSummarySerializer(
            read_only=True,
        )
    )

    reply_to = (
        MessageReplySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = Message

        fields = (
            "id",
            "author",
            "content",
            "reply_to",
            "is_edited",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class MessageCreateSerializer(
    serializers.Serializer,
):
    content = (
        serializers.CharField(
            max_length=4000,
            trim_whitespace=True,
        )
    )

    reply_to_id = (
        serializers.UUIDField(
            required=False,
            allow_null=True,
        )
    )


class MessageUpdateSerializer(
    serializers.Serializer,
):
    content = (
        serializers.CharField(
            max_length=4000,
            trim_whitespace=True,
        )
    )