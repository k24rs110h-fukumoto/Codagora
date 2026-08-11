import os

from django.core.exceptions import (
    ImproperlyConfigured,
)

from .base import *


def env_list(
    name,
    *,
    default="",
):
    value = os.getenv(
        name,
        default,
    )

    return [
        item.strip()
        for item
        in value.split(",")
        if item.strip()
    ]


def env_bool(
    name,
    *,
    default=False,
):
    value = os.getenv(name)

    if value is None:
        return default

    return (
        value
        .strip()
        .lower()
        in (
            "1",
            "true",
            "yes",
            "on",
        )
    )


def env_int(
    name,
    *,
    default,
):
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)

    except ValueError as error:
        raise ImproperlyConfigured(
            f"{name} must be an integer."
        ) from error


DEBUG = False


SECRET_KEY = os.environ[
    "DJANGO_SECRET_KEY"
]


ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS"
)

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS is required "
        "in production."
    )


CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS"
)


CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS"
)

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = env_bool(
    "DJANGO_CORS_ALLOW_CREDENTIALS",
    default=False,
)


DATABASES = {
    "default": {
        "ENGINE": (
            "django.db.backends.postgresql"
        ),
        "NAME": os.environ[
            "POSTGRES_DB"
        ],
        "USER": os.environ[
            "POSTGRES_USER"
        ],
        "PASSWORD": os.environ[
            "POSTGRES_PASSWORD"
        ],
        "HOST": os.environ[
            "POSTGRES_HOST"
        ],
        "PORT": os.getenv(
            "POSTGRES_PORT",
            "5432",
        ),
        "CONN_MAX_AGE": env_int(
            "POSTGRES_CONN_MAX_AGE",
            default=60,
        ),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "sslmode": os.getenv(
                "POSTGRES_SSLMODE",
                "require",
            ),
        },
    }
}


SECURE_SSL_REDIRECT = True

if env_bool(
    "DJANGO_TRUST_X_FORWARDED_PROTO",
    default=False,
):
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = (
    "codagora_sessionid"
)


CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = (
    "codagora_csrftoken"
)


SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = (
    "same-origin"
)

SECURE_CROSS_ORIGIN_OPENER_POLICY = (
    "same-origin"
)

X_FRAME_OPTIONS = "DENY"


SECURE_HSTS_SECONDS = env_int(
    "DJANGO_HSTS_SECONDS",
    default=3600,
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    env_bool(
        "DJANGO_HSTS_INCLUDE_SUBDOMAINS",
        default=False,
    )
)

SECURE_HSTS_PRELOAD = env_bool(
    "DJANGO_HSTS_PRELOAD",
    default=False,
)


FIREBASE_CHECK_REVOKED = True


GITHUB_APP_CALLBACK_URL = (
    os.environ[
        "GITHUB_APP_CALLBACK_URL"
    ]
)

if not GITHUB_APP_CALLBACK_URL.startswith(
    "https://"
):
    raise ImproperlyConfigured(
        "GITHUB_APP_CALLBACK_URL must "
        "use HTTPS in production."
    )


BLOB_READ_WRITE_TOKEN = (
    os.getenv(
        "BLOB_READ_WRITE_TOKEN",
        "",
    )
    .strip()
)

if not BLOB_READ_WRITE_TOKEN:
    raise ImproperlyConfigured(
        "BLOB_READ_WRITE_TOKEN is required "
        "in production."
    )


STORAGES = {
    "default": {
        "BACKEND": (
            "workspace_files."
            "vercel_storage."
            "VercelBlobStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles."
            "storage.StaticFilesStorage"
        ),
    },
}


LOG_LEVEL = os.getenv(
    "DJANGO_LOG_LEVEL",
    "INFO",
).upper()


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": (
                "{levelname} "
                "{asctime} "
                "{name} "
                "{message}"
            ),
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": (
                "logging.StreamHandler"
            ),
            "formatter": "standard",
        },
    },

    "root": {
        "handlers": [
            "console",
        ],
        "level": LOG_LEVEL,
    },

    "loggers": {
        "django": {
            "handlers": [
                "console",
            ],
            "level": LOG_LEVEL,
            "propagate": False,
        },

        "django.request": {
            "handlers": [
                "console",
            ],
            "level": "WARNING",
            "propagate": False,
        },

        "django.security": {
            "handlers": [
                "console",
            ],
            "level": "WARNING",
            "propagate": False,
        },
    },
}