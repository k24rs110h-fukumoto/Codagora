from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from rest_framework import serializers

from workspaces.serializers import (
    WorkspaceUserSummarySerializer,
)

from .models import (
    CalendarEvent,
    CalendarEventParticipant,
    ParticipantResponse,
    RecurrenceFrequency,
)


class CalendarParticipantSerializer(
    serializers.ModelSerializer,
):
    user = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = (
            CalendarEventParticipant
        )

        fields = (
            "id",
            "user",
            "response",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields


class CalendarEventSerializer(
    serializers.ModelSerializer,
):
    created_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    participants = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = CalendarEvent

        fields = (
            "id",
            "title",
            "description",
            "location_name",
            "timezone",
            "is_all_day",
            "starts_at",
            "ends_at",
            "start_date",
            "end_date",
            "recurrence_frequency",
            "recurrence_interval",
            "recurrence_weekdays",
            "recurrence_until",
            "participants",
            "created_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_participants(
        self,
        obj,
    ):
        participants = getattr(
            obj,
            "prefetched_participants",
            None,
        )

        if participants is None:
            participants = (
                obj.event_participants
                .select_related(
                    "user",
                )
                .all()
            )

        return (
            CalendarParticipantSerializer(
                participants,
                many=True,
            ).data
        )


class CalendarEventWriteSerializer(
    serializers.Serializer,
):
    title = serializers.CharField(
        max_length=160,
        trim_whitespace=True,
    )

    description = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            default="",
            trim_whitespace=True,
        )
    )

    location_name = (
        serializers.CharField(
            max_length=255,
            required=False,
            allow_blank=True,
            default="",
            trim_whitespace=True,
        )
    )

    timezone = serializers.CharField(
        max_length=64,
        default="Asia/Tokyo",
    )

    is_all_day = (
        serializers.BooleanField(
            default=False,
        )
    )

    starts_at = (
        serializers.DateTimeField(
            required=False,
            allow_null=True,
        )
    )

    ends_at = (
        serializers.DateTimeField(
            required=False,
            allow_null=True,
        )
    )

    start_date = (
        serializers.DateField(
            required=False,
            allow_null=True,
        )
    )

    end_date = (
        serializers.DateField(
            required=False,
            allow_null=True,
        )
    )

    recurrence_frequency = (
        serializers.ChoiceField(
            choices=(
                RecurrenceFrequency.choices
            ),
            default=(
                RecurrenceFrequency.NONE
            ),
        )
    )

    recurrence_interval = (
        serializers.IntegerField(
            min_value=1,
            max_value=365,
            default=1,
        )
    )

    recurrence_weekdays = (
        serializers.ListField(
            child=(
                serializers.IntegerField(
                    min_value=0,
                    max_value=6,
                )
            ),
            required=False,
            allow_empty=True,
            default=list,
        )
    )

    recurrence_until = (
        serializers.DateField(
            required=False,
            allow_null=True,
        )
    )

    participant_ids = (
        serializers.ListField(
            child=(
                serializers.UUIDField()
            ),
            required=False,
            allow_empty=True,
            default=list,
        )
    )

    def validate_timezone(
        self,
        value,
    ):
        try:
            ZoneInfo(value)

        except ZoneInfoNotFoundError:
            raise serializers.ValidationError(
                "存在しないTimezoneです。"
            )

        return value

    def validate_participant_ids(
        self,
        value,
    ):
        if len(value) != len(
            set(value)
        ):
            raise (
                serializers.ValidationError(
                    "参加者が重複しています。"
                )
            )

        return value

    def validate_recurrence_weekdays(
        self,
        value,
    ):
        if len(value) != len(
            set(value)
        ):
            raise (
                serializers.ValidationError(
                    "曜日が重複しています。"
                )
            )

        return sorted(value)

    def validate(
        self,
        attrs,
    ):
        is_all_day = attrs[
            "is_all_day"
        ]

        if is_all_day:
            if (
                not attrs.get(
                    "start_date"
                )
                or not attrs.get(
                    "end_date"
                )
            ):
                raise (
                    serializers.ValidationError(
                        "終日予定では"
                        "start_dateとend_date"
                        "が必要です。"
                    )
                )

            if (
                attrs["end_date"]
                < attrs["start_date"]
            ):
                raise (
                    serializers.ValidationError(
                        "end_dateはstart_date"
                        "以降にしてください。"
                    )
                )

            attrs["starts_at"] = None
            attrs["ends_at"] = None

            base_date = attrs[
                "start_date"
            ]

        else:
            if (
                not attrs.get(
                    "starts_at"
                )
                or not attrs.get(
                    "ends_at"
                )
            ):
                raise (
                    serializers.ValidationError(
                        "通常予定では"
                        "starts_atとends_at"
                        "が必要です。"
                    )
                )

            if (
                attrs["ends_at"]
                <= attrs["starts_at"]
            ):
                raise (
                    serializers.ValidationError(
                        "終了時刻は開始時刻より"
                        "後にしてください。"
                    )
                )

            attrs["start_date"] = None
            attrs["end_date"] = None

            timezone_info = ZoneInfo(
                attrs["timezone"]
            )

            base_date = (
                attrs["starts_at"]
                .astimezone(
                    timezone_info
                )
                .date()
            )

        frequency = attrs[
            "recurrence_frequency"
        ]

        if (
            frequency
            == RecurrenceFrequency.NONE
        ):
            attrs[
                "recurrence_interval"
            ] = 1

            attrs[
                "recurrence_weekdays"
            ] = []

            attrs[
                "recurrence_until"
            ] = None

        elif (
            frequency
            == RecurrenceFrequency.WEEKLY
        ):
            if not attrs[
                "recurrence_weekdays"
            ]:
                attrs[
                    "recurrence_weekdays"
                ] = [
                    base_date.weekday()
                ]

        else:
            attrs[
                "recurrence_weekdays"
            ] = []

        recurrence_until = attrs.get(
            "recurrence_until"
        )

        if (
            recurrence_until
            and recurrence_until
            < base_date
        ):
            raise (
                serializers.ValidationError(
                    "繰り返し終了日は"
                    "予定開始日以降に"
                    "してください。"
                )
            )

        return attrs


class CalendarParticipantResponseSerializer(
    serializers.Serializer,
):
    response = serializers.ChoiceField(
        choices=ParticipantResponse.choices,
    )


class CalendarOccurrenceRangeSerializer(
    serializers.Serializer,
):
    start = serializers.DateField()
    end = serializers.DateField()

    def validate(
        self,
        attrs,
    ):
        start = attrs["start"]
        end = attrs["end"]

        if end < start:
            raise (
                serializers.ValidationError(
                    "endはstart以降に"
                    "してください。"
                )
            )

        if (
            end - start
        ).days > 366:
            raise (
                serializers.ValidationError(
                    "一度に取得できる期間は"
                    "最大366日です。"
                )
            )

        return attrs


class CalendarOccurrenceSerializer(
    serializers.Serializer,
):
    event = CalendarEventSerializer()

    occurrence_key = (
        serializers.CharField()
    )

    is_all_day = (
        serializers.BooleanField()
    )

    start_date = (
        serializers.DateField(
            allow_null=True,
        )
    )

    end_date = (
        serializers.DateField(
            allow_null=True,
        )
    )

    starts_at = (
        serializers.DateTimeField(
            allow_null=True,
        )
    )

    ends_at = (
        serializers.DateTimeField(
            allow_null=True,
        )
    )