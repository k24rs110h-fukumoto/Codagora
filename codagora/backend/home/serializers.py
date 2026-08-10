from rest_framework import serializers


class HomeResponseSerializer(
    serializers.Serializer
):
    continue_working = (
        serializers.DictField(
            allow_null=True,
        )
    )

    today = serializers.DictField()

    project_pulse = (
        serializers.ListField(
            child=(
                serializers.DictField()
            )
        )
    )

    next_move = (
        serializers.DictField()
    )

    active_workspaces = (
        serializers.ListField(
            child=(
                serializers.DictField()
            )
        )
    )

    unread_notifications = (
        serializers.IntegerField()
    )

    generated_at = (
        serializers.DateTimeField()
    )