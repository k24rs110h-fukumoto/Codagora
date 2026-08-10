import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-development-only-key",
)

DEBUG = False

ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "accounts",
    "workspaces",
    "chat.apps.ChatConfig",
    "tasks.apps.TasksConfig",
    "scheduling.apps.SchedulingConfig",
    "workspace_files.apps.WorkspaceFilesConfig",
    "locations.apps.LocationsConfig",
    "integrations.apps.IntegrationsConfig",
    "activity.apps.ActivityConfig",
    "notifications.apps.NotificationsConfig",
    "home.apps.HomeConfig",
    "explore.apps.ExploreConfig",
    "profiles.apps.ProfilesConfig",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "ja"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_URLS_REGEX = r"^/api/.*$"

AUTH_USER_MODEL = "accounts.User"

FIREBASE_PROJECT_ID = os.getenv(
    "FIREBASE_PROJECT_ID",
    "",
)

FIREBASE_CHECK_REVOKED = (
    os.getenv(
        "FIREBASE_CHECK_REVOKED",
        "False",
    )
    .lower()
    == "true"
)

CODAGORA_TERMS_VERSION = os.getenv(
    "CODAGORA_TERMS_VERSION",
    "1.0",
)

CODAGORA_PRIVACY_VERSION = os.getenv(
    "CODAGORA_PRIVACY_VERSION",
    "1.0",
)

CODAGORA_RECENT_AUTH_SECONDS = int(
    os.getenv(
        "CODAGORA_RECENT_AUTH_SECONDS",
        "300",
    )
)

CODAGORA_ACCOUNT_DELETION_GRACE_DAYS = int(
    os.getenv(
        "CODAGORA_ACCOUNT_DELETION_GRACE_DAYS",
        "7",
    )
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        (
            "accounts.authentication."
            "FirebaseAuthentication"
        ),
        (
            "rest_framework.authentication."
            "SessionAuthentication"
        ),
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        (
            "accounts.permissions."
            "IsActiveCodagoraUser"
        ),
    ],

    "DEFAULT_THROTTLE_CLASSES": [
        (
            "rest_framework.throttling."
            "AnonRateThrottle"
        ),
        (
            "rest_framework.throttling."
            "UserRateThrottle"
        ),
        (
            "rest_framework.throttling."
            "ScopedRateThrottle"
        ),
    ],

    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "3000/hour",
        "auth_sensitive": "20/hour",
        "account_delete": "3/day",
    },
}

MEDIA_ROOT = (
    BASE_DIR
    / "media"
)

MEDIA_URL = "/media/"

WORKSPACE_FILE_MAX_UPLOAD_SIZE_BYTES = int(
    os.getenv(
        "WORKSPACE_FILE_MAX_UPLOAD_SIZE_BYTES",
        str(
            50
            * 1024
            * 1024
        ),
    )
)

WORKSPACE_FILE_TRASH_RETENTION_DAYS = int(
    os.getenv(
        "WORKSPACE_FILE_TRASH_RETENTION_DAYS",
        "30",
    )
)

LOCATION_SHARE_DEFAULT_DURATION_MINUTES = int(
    os.getenv(
        "LOCATION_SHARE_DEFAULT_DURATION_MINUTES",
        "240",
    )
)

LOCATION_SHARE_MAX_DURATION_MINUTES = int(
    os.getenv(
        "LOCATION_SHARE_MAX_DURATION_MINUTES",
        "1440",
    )
)

LOCATION_SHARE_HISTORY_RETENTION_DAYS = int(
    os.getenv(
        "LOCATION_SHARE_HISTORY_RETENTION_DAYS",
        "7",
    )
)

CODAGORA_TOKEN_ENCRYPTION_KEY = os.getenv(
    "CODAGORA_TOKEN_ENCRYPTION_KEY",
    "",
)

GITHUB_APP_CLIENT_ID = os.getenv(
    "GITHUB_APP_CLIENT_ID",
    "",
)

GITHUB_APP_CLIENT_SECRET = os.getenv(
    "GITHUB_APP_CLIENT_SECRET",
    "",
)

GITHUB_APP_SLUG = os.getenv(
    "GITHUB_APP_SLUG",
    "",
)

GITHUB_APP_CALLBACK_URL = os.getenv(
    "GITHUB_APP_CALLBACK_URL",
    "",
)

GITHUB_APP_PRIVATE_KEY = os.getenv(
    "GITHUB_APP_PRIVATE_KEY",
    "",
)

GITHUB_APP_PRIVATE_KEY_PATH = os.getenv(
    "GITHUB_APP_PRIVATE_KEY_PATH",
    "",
)

GITHUB_APP_MOBILE_REDIRECT_URL = os.getenv(
    "GITHUB_APP_MOBILE_REDIRECT_URL",
    "",
)

GITHUB_API_BASE_URL = (
    "https://api.github.com"
)

GITHUB_API_VERSION = os.getenv(
    "GITHUB_API_VERSION",
    "2026-03-10",
)

GITHUB_OAUTH_STATE_MINUTES = int(
    os.getenv(
        "GITHUB_OAUTH_STATE_MINUTES",
        "10",
    )
)
