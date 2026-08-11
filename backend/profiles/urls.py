from django.urls import path

from .views import (
    MyProfileView,
    PublicProfileProjectsView,
    PublicProfileView,
)


app_name = "profiles"


urlpatterns = [
    path(
        "me/",
        MyProfileView.as_view(),
        name="me",
    ),

    path(
        "<str:handle>/projects/",
        PublicProfileProjectsView.as_view(),
        name="projects",
    ),

    path(
        "<str:handle>/",
        PublicProfileView.as_view(),
        name="detail",
    ),
]