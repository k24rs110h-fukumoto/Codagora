from django.urls import path

from .views import (
    GitHubCallbackView,
    GitHubSetupView,
)


app_name = "integrations"


urlpatterns = [
    path(
        "github/setup/",
        GitHubSetupView.as_view(),
        name="github-setup",
    ),

    path(
        "github/callback/",
        GitHubCallbackView.as_view(),
        name="github-callback",
    ),
]