from rest_framework.pagination import (
    CursorPagination,
)


class TaskCursorPagination(
    CursorPagination,
):
    page_size = 50

    page_size_query_param = (
        "page_size"
    )

    max_page_size = 100

    ordering = "-updated_at"


class TaskCommentCursorPagination(
    CursorPagination,
):
    page_size = 50

    page_size_query_param = (
        "page_size"
    )

    max_page_size = 100

    ordering = "created_at"