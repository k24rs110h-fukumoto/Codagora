from django.urls import path

from .views import (
    CurrentWorkspaceLocationShareView,
    WorkspaceLocationShareListView,
    WorkspacePlaceDetailView,
    WorkspacePlaceListCreateView,
)


app_name = "locations"


urlpatterns = [
    path(
        "places/",
        WorkspacePlaceListCreateView.as_view(),
        name="place-list-create",
    ),

    path(
        "places/<uuid:place_id>/",
        WorkspacePlaceDetailView.as_view(),
        name="place-detail",
    ),

    path(
        "shares/",
        WorkspaceLocationShareListView.as_view(),
        name="location-share-list-create",
    ),

    path(
        "shares/me/",
        CurrentWorkspaceLocationShareView.as_view(),
        name="current-location-share",
    ),
]