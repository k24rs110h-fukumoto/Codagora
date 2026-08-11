from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/",
        include(
            "core.urls"
        ),
    ),

    path(
        "api/v1/auth/",
        include(
            "accounts.auth_urls"
        ),
    ),

    path(
        "api/v1/accounts/",
        include(
            "accounts.urls"
        ),
    ),

    path(
        "api/v1/workspaces/",
        include(
            "workspaces.urls"
        ),
    ),

    path(
        "api/v1/workspaces/",
        include(
            "activity.workspace_urls"
        ),
    ),

    path(
        "api/v1/integrations/",
        include(
            "integrations.urls"
        ),
    ),

    path(
        "api/v1/activity/",
        include(
            "activity.urls"
        ),
    ),

    path(
        "api/v1/notifications/",
        include(
            "notifications.urls"
        ),
    ),

    path(
        "api/v1/home/",
        include(
            "home.urls"
        ),
    ),

    path(
        "api/v1/explore/",
        include(
            "explore.urls"
        ),
    ),

    path(
        "api/v1/profiles/",
        include(
            "profiles.urls"
        ),
    ),

    path(
        "api/v1/files/",
        include(
            "workspace_files.download_urls"
        ),
    ),

    path(
        "api-auth/",
        include(
            "rest_framework.urls"
        ),
    ),
]