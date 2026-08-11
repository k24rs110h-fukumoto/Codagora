from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

from rest_framework.exceptions import (
    ValidationError,
)


def get_decoded_token(request):
    if not isinstance(
        request.auth,
        dict,
    ):
        raise ValidationError(
            {
                "detail": (
                    "このAPIはFirebase認証"
                    "が必要です。"
                )
            }
        )

    return request.auth


def raise_drf_validation_error(
    error: DjangoValidationError,
):
    if hasattr(
        error,
        "message_dict",
    ):
        raise ValidationError(
            error.message_dict
        ) from error

    raise ValidationError(
        {
            "detail": error.messages,
        }
    ) from error