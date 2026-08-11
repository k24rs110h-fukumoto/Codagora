import os

from urllib.parse import (
    unquote,
    urlparse,
)


def configure_render_database():
    database_url = os.getenv(
        "DATABASE_URL",
        "",
    ).strip()

    if not database_url:
        return

    parsed = urlparse(
        database_url
    )

    if parsed.scheme not in (
        "postgres",
        "postgresql",
    ):
        return

    database_name = (
        parsed.path.lstrip("/")
    )

    if database_name:
        os.environ.setdefault(
            "POSTGRES_DB",
            unquote(
                database_name
            ),
        )

    if parsed.username:
        os.environ.setdefault(
            "POSTGRES_USER",
            unquote(
                parsed.username
            ),
        )

    if parsed.password:
        os.environ.setdefault(
            "POSTGRES_PASSWORD",
            unquote(
                parsed.password
            ),
        )

    if parsed.hostname:
        os.environ.setdefault(
            "POSTGRES_HOST",
            parsed.hostname,
        )

    os.environ.setdefault(
        "POSTGRES_PORT",
        str(
            parsed.port
            or 5432
        ),
    )


def configure_render_hostname():
    hostname = os.getenv(
        "RENDER_EXTERNAL_HOSTNAME",
        "",
    ).strip()

    if not hostname:
        return

    os.environ.setdefault(
        "DJANGO_ALLOWED_HOSTS",
        hostname,
    )

    os.environ.setdefault(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        f"https://{hostname}",
    )

    os.environ.setdefault(
        "GITHUB_APP_CALLBACK_URL",
        (
            f"https://{hostname}"
            "/api/v1/integrations/"
            "github/callback/"
        ),
    )


configure_render_database()
configure_render_hostname()


from .production import *


render_hostname = os.getenv(
    "RENDER_EXTERNAL_HOSTNAME",
    "",
).strip()


MIDDLEWARE = list(
    MIDDLEWARE
)

security_middleware = (
    "django.middleware.security."
    "SecurityMiddleware"
)

whitenoise_middleware = (
    "whitenoise.middleware."
    "WhiteNoiseMiddleware"
)

if (
    whitenoise_middleware
    not in MIDDLEWARE
):
    if (
        security_middleware
        in MIDDLEWARE
    ):
        security_index = (
            MIDDLEWARE.index(
                security_middleware
            )
        )

        MIDDLEWARE.insert(
            security_index + 1,
            whitenoise_middleware,
        )

    else:
        MIDDLEWARE.insert(
            0,
            whitenoise_middleware,
        )


STATIC_ROOT = (
    BASE_DIR
    / "staticfiles"
)


STORAGES = {
    **STORAGES,

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


if render_hostname:
    render_origin = (
        f"https://{render_hostname}"
    )

    if (
        render_hostname
        not in ALLOWED_HOSTS
    ):
        ALLOWED_HOSTS.append(
            render_hostname
        )

    if (
        render_origin
        not in CSRF_TRUSTED_ORIGINS
    ):
        CSRF_TRUSTED_ORIGINS.append(
            render_origin
        )