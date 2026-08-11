from django.urls import path

from .views import (
    TaskCommentDetailView,
    TaskCommentListCreateView,
    TaskDetailView,
    TaskListCreateView,
    TaskReorderView,
)


app_name = "tasks"


urlpatterns = [
    path(
        "",
        TaskListCreateView.as_view(),
        name="task-list-create",
    ),

    path(
        "reorder/",
        TaskReorderView.as_view(),
        name="task-reorder",
    ),

    path(
        "<uuid:task_id>/",
        TaskDetailView.as_view(),
        name="task-detail",
    ),

    path(
        "<uuid:task_id>/comments/",
        TaskCommentListCreateView.as_view(),
        name="task-comment-list-create",
    ),

    path(
        (
            "<uuid:task_id>/comments/"
            "<uuid:comment_id>/"
        ),
        TaskCommentDetailView.as_view(),
        name="task-comment-detail",
    ),
]