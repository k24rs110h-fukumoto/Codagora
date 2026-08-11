from decimal import Decimal

from rest_framework import serializers

from workspaces.serializers import (
    WorkspaceUserSummarySerializer,
)

from .models import (
    WorkspaceLocationShare,
    WorkspacePlace,
)


class WorkspacePlaceSerializer(
    serializers.ModelSerializer,
):
    created_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    latitude = serializers.FloatField(
        read_only=True,
    )

    longitude = serializers.FloatField(
        read_only=True,
    )

    class Meta:
        model = WorkspacePlace

        fields = (
            "id",
            "name",
            "description",
            "address",
            "latitude",
            "longitude",
            "created_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class WorkspacePlaceWriteSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=120,
        trim_whitespace=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    address = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
    )


class WorkspacePlaceUpdateSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=120,
        required=False,
        trim_whitespace=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    address = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
        required=False,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
        required=False,
    )

    def validate(
        self,
        attrs,
    ):
        if not attrs:
            raise serializers.ValidationError(
                "変更する項目を"
                "指定してください。"
            )

        return attrs


class WorkspaceLocationShareSerializer(
    serializers.ModelSerializer,
):
    user = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    place = (
        WorkspacePlaceSerializer(
            read_only=True,
        )
    )

    latitude = serializers.FloatField(
        read_only=True,
    )

    longitude = serializers.FloatField(
        read_only=True,
    )

    class Meta:
        model = WorkspaceLocationShare

        fields = (
            "id",
            "user",
            "place",
            "label",
            "note",
            "latitude",
            "longitude",
            "accuracy_meters",
            "started_at",
            "expires_at",
            "updated_at",
        )

        read_only_fields = fields


class WorkspaceLocationShareCreateSerializer(
    serializers.Serializer,
):
    place_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    label = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
        required=False,
        allow_null=True,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
        required=False,
        allow_null=True,
    )

    accuracy_meters = (
        serializers.IntegerField(
            min_value=0,
            max_value=100000,
            required=False,
            allow_null=True,
        )
    )

    duration_minutes = (
        serializers.IntegerField(
            min_value=15,
            required=False,
        )
    )

    def validate(
        self,
        attrs,
    ):
        place_id = attrs.get(
            "place_id"
        )

        latitude = attrs.get(
            "latitude"
        )

        longitude = attrs.get(
            "longitude"
        )

        if place_id is None:
            if (
                latitude is None
                or longitude is None
            ):
                raise serializers.ValidationError(
                    "保存地点を指定しない場合は"
                    "latitudeとlongitudeが"
                    "必要です。"
                )

        if (
            latitude is None
            and longitude is not None
        ):
            raise serializers.ValidationError(
                "latitudeを指定してください。"
            )

        if (
            latitude is not None
            and longitude is None
        ):
            raise serializers.ValidationError(
                "longitudeを指定してください。"
            )

        return attrs