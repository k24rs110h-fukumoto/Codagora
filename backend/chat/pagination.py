from rest_framework.pagination import (
    CursorPagination,
)


class MessageCursorPagination(
    CursorPagination,
):
    page_size = 50

    max_page_size = 100

    ordering = (
        "-created_at"
    )

    page_size_query_param = (
        "page_size"
    )