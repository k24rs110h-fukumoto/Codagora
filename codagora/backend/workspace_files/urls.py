from django.urls import path

from .views import (
    WorkspaceFileDetailView,
    WorkspaceFileDownloadView,
    WorkspaceFileListCreateView,
    WorkspaceFileRestoreView,
    WorkspaceFolderDetailView,
    WorkspaceFolderListCreateView,
    WorkspaceFolderRestoreView,
    WorkspaceTrashView,
)


app_name = "workspace_files"


urlpatterns = [
    path(
        "",
        WorkspaceFileListCreateView.as_view(),
        name="file-list-create",
    ),

    path(
        "folders/",
        WorkspaceFolderListCreateView.as_view(),
        name="folder-list-create",
    ),

    path(
        "trash/",
        WorkspaceTrashView.as_view(),
        name="trash",
    ),

    path(
        "folders/<uuid:folder_id>/",
        WorkspaceFolderDetailView.as_view(),
        name="folder-detail",
    ),

    path(
        (
            "folders/"
            "<uuid:folder_id>/restore/"
        ),
        WorkspaceFolderRestoreView.as_view(),
        name="folder-restore",
    ),

    path(
        "<uuid:file_id>/",
        WorkspaceFileDetailView.as_view(),
        name="file-detail",
    ),

    path(
        "<uuid:file_id>/download/",
        WorkspaceFileDownloadView.as_view(),
        name="file-download",
    ),

    path(
        "<uuid:file_id>/restore/",
        WorkspaceFileRestoreView.as_view(),
        name="file-restore",
    ),
]