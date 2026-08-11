import re

from rest_framework import serializers


class OnboardingCompleteSerializer(
    serializers.Serializer,
):
    display_name = serializers.CharField(
        max_length=100,
        trim_whitespace=True,
    )

    handle = serializers.CharField(
        min_length=3,
        max_length=30,
        trim_whitespace=True,
    )

    accept_terms = (
        serializers.BooleanField()
    )

    accept_privacy = (
        serializers.BooleanField()
    )

    def validate_handle(
        self,
        value,
    ):
        normalized = (
            value
            .strip()
            .lower()
        )

        if not re.fullmatch(
            r"[a-z0-9_]{3,30}",
            normalized,
        ):
            raise (
                serializers.ValidationError(
                    "handleは英小文字・"
                    "数字・_のみ"
                    "使用できます。"
                )
            )

        return normalized


class LegalAcceptanceSerializer(
    serializers.Serializer,
):
    accept_terms = (
        serializers.BooleanField()
    )

    accept_privacy = (
        serializers.BooleanField()
    )


class ProviderUnlinkSerializer(
    serializers.Serializer,
):
    provider_id = (
        serializers.CharField(
            max_length=100,
            trim_whitespace=True,
        )
    )