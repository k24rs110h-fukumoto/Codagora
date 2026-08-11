from django.conf import settings

from rest_framework import serializers

from workspaces.serializers import (
    WorkspaceUserSummarySerializer,
)

from .models import (
    WorkspaceFile,
    WorkspaceFolder,
)


class WorkspaceFolderSerializer(
    serializers.ModelSerializer,
):
    created_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    deleted_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    parent_id = serializers.UUIDField(
        source="parent.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = WorkspaceFolder

        fields = (
            "id",
            "name",
            "parent_id",
            "created_by",
            "deleted_at",
            "deleted_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class WorkspaceFileSerializer(
    serializers.ModelSerializer,
):
    uploaded_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    deleted_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    folder_id = serializers.UUIDField(
        source="folder.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = WorkspaceFile

        fields = (
            "id",
            "folder_id",
            "original_name",
            "display_name",
            "content_type",
            "size_bytes",
            "sha256",
            "uploaded_by",
            "deleted_at",
            "deleted_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class WorkspaceFolderCreateSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
    )

    parent_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )


class WorkspaceFolderUpdateSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=255,
        required=False,
        trim_whitespace=True,
    )

    parent_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    def validate(
        self,
        attrs,
    ):
        if not attrs:
            raise serializers.ValidationError(
                "変更内容を指定してください。"
            )

        return attrs


class WorkspaceFileUploadSerializer(
    serializers.Serializer,
):
    file = serializers.FileField()

    folder_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    display_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    def validate_file(
        self,
        value,
    ):
        maximum = (
            settings
            .WORKSPACE_FILE_MAX_UPLOAD_SIZE_BYTES
        )

        if value.size > maximum:
            megabytes = (
                maximum
                // 1024
                // 1024
            )

            raise serializers.ValidationError(
                f"ファイルサイズは"
                f"{megabytes}MB以下に"
                "してください。"
            )

        return value


class WorkspaceFileUpdateSerializer(
    serializers.Serializer,
):
    display_name = (
        serializers.CharField(
            max_length=255,
            required=False,
            trim_whitespace=True,
        )
    )

    folder_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    def validate(
        self,
        attrs,
    ):
        if not attrs:
            raise serializers.ValidationError(
                "変更内容を指定してください。"
            )

        return attrs


class WorkspaceLocationQuerySerializer(
    serializers.Serializer,
):
    folder_id = serializers.UUIDField(
        required=False,
    )