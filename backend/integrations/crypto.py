from cryptography.fernet import (
    Fernet,
    InvalidToken,
)
from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
)


def get_fernet():
    key = (
        settings
        .CODAGORA_TOKEN_ENCRYPTION_KEY
    )

    if not key:
        raise ImproperlyConfigured(
            "CODAGORA_TOKEN_ENCRYPTION_KEY "
            "is not configured."
        )

    try:
        return Fernet(
            key.encode("utf-8")
        )

    except Exception as error:
        raise ImproperlyConfigured(
            "CODAGORA_TOKEN_ENCRYPTION_KEY "
            "is invalid."
        ) from error


def encrypt_secret(
    value,
):
    if not value:
        return ""

    return (
        get_fernet()
        .encrypt(
            value.encode("utf-8")
        )
        .decode("utf-8")
    )


def decrypt_secret(
    value,
):
    if not value:
        return ""

    try:
        return (
            get_fernet()
            .decrypt(
                value.encode(
                    "utf-8"
                )
            )
            .decode(
                "utf-8"
            )
        )

    except InvalidToken as error:
        raise ImproperlyConfigured(
            "Encrypted token could not "
            "be decrypted."
        ) from error