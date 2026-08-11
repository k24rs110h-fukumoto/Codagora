from django.urls import path

from .download_views import (
    WorkspaceFileDownloadView,
)


app_name = "workspace_file_downloads"


urlpatterns = [
    path(
        "<uuid:file_id>/download/",
        WorkspaceFileDownloadView.as_view(),
        name="download",
    ),
]