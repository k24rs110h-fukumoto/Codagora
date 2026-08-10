from django.urls import path

from .views import (
    WorkspaceActivityListView,
)


app_name = "workspace_activity"


urlpatterns = [
    path(
        "<str:workspace_slug>/activity/",
        WorkspaceActivityListView.as_view(),
        name="list",
    ),
]