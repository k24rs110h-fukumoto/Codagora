from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import status
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import (
    Response,
)
from rest_framework.views import (
    APIView,
)

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from workspaces.selectors import (
    get_accessible_workspaces,
)

from .models import (
    TaskComment,
)
from .pagination import (
    TaskCommentCursorPagination,
    TaskCursorPagination,
)
from .selectors import (
    filter_workspace_tasks,
    get_task_comments,
    get_workspace_tasks,
)
from .serializers import (
    TaskCommentSerializer,
    TaskCommentWriteSerializer,
    TaskCreateSerializer,
    TaskFilterSerializer,
    TaskReorderSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)
from .services import (
    create_task,
    create_task_comment,
    delete_task,
    delete_task_comment,
    reorder_tasks,
    update_task,
    update_task_comment,
)


def raise_drf_validation_error(
    error,
):
    if hasattr(
        error,
        "message_dict",
    ):
        raise ValidationError(
            error.message_dict
        ) from error

    raise ValidationError(
        {
            "detail": error.messages,
        }
    ) from error


def handle_service_error(
    error,
):
    if isinstance(
        error,
        DjangoPermissionDenied,
    ):
        raise PermissionDenied(
            detail=str(error),
        ) from error

    if isinstance(
        error,
        DjangoValidationError,
    ):
        raise_drf_validation_error(
            error
        )

    raise error


class WorkspaceTaskMixin:
    def get_workspace(self):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=self.kwargs[
                "workspace_slug"
            ],
        )

    def get_task(self):
        workspace = (
            self.get_workspace()
        )

        return get_object_or_404(
            get_workspace_tasks(
                workspace=workspace,
            ),
            id=self.kwargs[
                "task_id"
            ],
        )


class TaskListCreateView(
    WorkspaceTaskMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    pagination_class = (
        TaskCursorPagination
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        filter_serializer = (
            TaskFilterSerializer(
                data=request.query_params,
            )
        )

        filter_serializer.is_valid(
            raise_exception=True,
        )

        queryset = (
            get_workspace_tasks(
                workspace=workspace,
            )
        )

        queryset = (
            filter_workspace_tasks(
                queryset=queryset,
                status=(
                    filter_serializer
                    .validated_data
                    .get("status")
                ),
                priority=(
                    filter_serializer
                    .validated_data
                    .get("priority")
                ),
                assignee_id=(
                    filter_serializer
                    .validated_data
                    .get(
                        "assignee_id"
                    )
                ),
                search=(
                    filter_serializer
                    .validated_data
                    .get("q")
                ),
                overdue=(
                    filter_serializer
                    .validated_data
                    .get("overdue")
                ),
            )
        )

        paginator = (
            self.pagination_class()
        )

        page = (
            paginator.paginate_queryset(
                queryset,
                request,
                view=self,
            )
        )

        return (
            paginator
            .get_paginated_response(
                TaskSerializer(
                    page,
                    many=True,
                ).data
            )
        )

    def post(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        serializer = (
            TaskCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            task = create_task(
                workspace=workspace,
                actor=request.user,
                title=(
                    serializer
                    .validated_data[
                        "title"
                    ]
                ),
                description=(
                    serializer
                    .validated_data[
                        "description"
                    ]
                ),
                status=(
                    serializer
                    .validated_data[
                        "status"
                    ]
                ),
                priority=(
                    serializer
                    .validated_data[
                        "priority"
                    ]
                ),
                assignee_ids=(
                    serializer
                    .validated_data[
                        "assignee_ids"
                    ]
                ),
                due_at=(
                    serializer
                    .validated_data
                    .get("due_at")
                ),
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        task = get_object_or_404(
            get_workspace_tasks(
                workspace=workspace,
            ),
            id=task.id,
        )

        return Response(
            TaskSerializer(
                task
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class TaskDetailView(
    WorkspaceTaskMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        task_id,
    ):
        return Response(
            TaskSerializer(
                self.get_task()
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        workspace_slug,
        task_id,
    ):
        task = self.get_task()

        serializer = (
            TaskUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            task = update_task(
                task=task,
                actor=request.user,
                changes=dict(
                    serializer
                    .validated_data
                ),
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        task = get_object_or_404(
            get_workspace_tasks(
                workspace=(
                    task.workspace
                ),
            ),
            id=task.id,
        )

        return Response(
            TaskSerializer(
                task
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        task_id,
    ):
        task = self.get_task()

        try:
            delete_task(
                task=task,
                actor=request.user,
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
            ),
        )


class TaskReorderView(
    WorkspaceTaskMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        serializer = (
            TaskReorderSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            tasks = reorder_tasks(
                workspace=workspace,
                actor=request.user,
                status=(
                    serializer
                    .validated_data[
                        "status"
                    ]
                ),
                task_ids=(
                    serializer
                    .validated_data[
                        "task_ids"
                    ]
                ),
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            TaskSerializer(
                tasks,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class TaskCommentListCreateView(
    WorkspaceTaskMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    pagination_class = (
        TaskCommentCursorPagination
    )

    def get(
        self,
        request,
        workspace_slug,
        task_id,
    ):
        task = self.get_task()

        queryset = (
            get_task_comments(
                task=task,
            )
        )

        paginator = (
            self.pagination_class()
        )

        page = (
            paginator.paginate_queryset(
                queryset,
                request,
                view=self,
            )
        )

        return (
            paginator
            .get_paginated_response(
                TaskCommentSerializer(
                    page,
                    many=True,
                ).data
            )
        )

    def post(
        self,
        request,
        workspace_slug,
        task_id,
    ):
        task = self.get_task()

        serializer = (
            TaskCommentWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            comment = (
                create_task_comment(
                    task=task,
                    actor=request.user,
                    content=(
                        serializer
                        .validated_data[
                            "content"
                        ]
                    ),
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            TaskCommentSerializer(
                comment
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class TaskCommentDetailView(
    WorkspaceTaskMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_comment(self):
        task = self.get_task()

        return get_object_or_404(
            TaskComment.objects
            .select_related(
                "task",
                "task__workspace",
                "author",
            ),
            id=self.kwargs[
                "comment_id"
            ],
            task=task,
            deleted_at__isnull=True,
        )

    def patch(
        self,
        request,
        workspace_slug,
        task_id,
        comment_id,
    ):
        comment = (
            self.get_comment()
        )

        serializer = (
            TaskCommentWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            comment = (
                update_task_comment(
                    comment=comment,
                    actor=request.user,
                    content=(
                        serializer
                        .validated_data[
                            "content"
                        ]
                    ),
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            TaskCommentSerializer(
                comment
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        task_id,
        comment_id,
    ):
        comment = (
            self.get_comment()
        )

        try:
            delete_task_comment(
                comment=comment,
                actor=request.user,
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
            ),
        )