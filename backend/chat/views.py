from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import (
    status,
)
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
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.selectors import (
    get_accessible_workspaces,
)

from .models import (
    Channel,
    Message,
)
from .pagination import (
    MessageCursorPagination,
)
from .selectors import (
    get_archived_channels,
    get_channel_messages,
    get_visible_channels,
)
from .serializers import (
    ChannelCreateSerializer,
    ChannelReorderSerializer,
    ChannelSerializer,
    ChannelUpdateSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    MessageUpdateSerializer,
)
from .services import (
    archive_channel,
    create_channel,
    create_message,
    delete_message,
    reorder_channels,
    restore_channel,
    update_channel,
    update_message,
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


def user_is_workspace_manager(
    *,
    workspace,
    user,
):
    if workspace.owner_id == user.id:
        return True

    return (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            role=(
                WorkspaceMember
                .Role
                .ADMIN
            ),
            is_active=True,
        )
        .exists()
    )


class WorkspaceChannelAccessMixin:
    def get_workspace(
        self,
    ):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=(
                self.kwargs[
                    "workspace_slug"
                ]
            ),
        )

    def get_active_channel(
        self,
    ):
        workspace = (
            self.get_workspace()
        )

        return get_object_or_404(
            Channel.objects
            .select_related(
                "workspace",
                "created_by",
            ),
            id=self.kwargs[
                "channel_id"
            ],
            workspace=workspace,
            is_archived=False,
        )

    def get_any_channel(
        self,
    ):
        workspace = (
            self.get_workspace()
        )

        return get_object_or_404(
            Channel.objects
            .select_related(
                "workspace",
                "created_by",
                "archived_by",
            ),
            id=self.kwargs[
                "channel_id"
            ],
            workspace=workspace,
        )


class ChannelListCreateView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        channels = (
            get_visible_channels(
                workspace=workspace,
            )
        )

        return Response(
            ChannelSerializer(
                channels,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
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
            ChannelCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            channel = create_channel(
                workspace=workspace,
                actor=request.user,
                name=(
                    serializer
                    .validated_data[
                        "name"
                    ]
                ),
                description=(
                    serializer
                    .validated_data
                    .get(
                        "description",
                        "",
                    )
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
            ChannelSerializer(
                channel
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class ArchivedChannelListView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        if not user_is_workspace_manager(
            workspace=workspace,
            user=request.user,
        ):
            raise PermissionDenied(
                "Archive済みChannelを"
                "確認できるのは"
                "OwnerまたはAdminのみです。"
            )

        channels = (
            get_archived_channels(
                workspace=workspace,
            )
        )

        return Response(
            ChannelSerializer(
                channels,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class ChannelDetailView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        channel_id,
    ):
        channel = (
            self.get_active_channel()
        )

        return Response(
            ChannelSerializer(
                channel
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        workspace_slug,
        channel_id,
    ):
        channel = (
            self.get_active_channel()
        )

        serializer = (
            ChannelUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            channel = update_channel(
                channel=channel,
                actor=request.user,
                name=(
                    serializer
                    .validated_data
                    .get("name")
                ),
                description=(
                    serializer
                    .validated_data
                    .get("description")
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
            ChannelSerializer(
                channel
            ).data,
            status=status.HTTP_200_OK,
        )


class ChannelArchiveView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        channel_id,
    ):
        channel = (
            self.get_any_channel()
        )

        try:
            channel = archive_channel(
                channel=channel,
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
            ChannelSerializer(
                channel
            ).data,
            status=status.HTTP_200_OK,
        )


class ChannelRestoreView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        channel_id,
    ):
        channel = (
            self.get_any_channel()
        )

        try:
            channel = restore_channel(
                channel=channel,
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
            ChannelSerializer(
                channel
            ).data,
            status=status.HTTP_200_OK,
        )


class ChannelReorderView(
    WorkspaceChannelAccessMixin,
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
            ChannelReorderSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            channels = reorder_channels(
                workspace=workspace,
                actor=request.user,
                channel_ids=(
                    serializer
                    .validated_data[
                        "channel_ids"
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
            ChannelSerializer(
                channels,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class MessageListCreateView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    pagination_class = (
        MessageCursorPagination
    )

    def get(
        self,
        request,
        workspace_slug,
        channel_id,
    ):
        channel = (
            self.get_active_channel()
        )

        queryset = (
            get_channel_messages(
                channel=channel,
            )
        )

        paginator = (
            self.pagination_class()
        )

        page = (
            paginator
            .paginate_queryset(
                queryset,
                request,
                view=self,
            )
        )

        serializer = (
            MessageSerializer(
                page,
                many=True,
            )
        )

        return (
            paginator
            .get_paginated_response(
                serializer.data
            )
        )

    def post(
        self,
        request,
        workspace_slug,
        channel_id,
    ):
        channel = (
            self.get_active_channel()
        )

        serializer = (
            MessageCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        reply_to = None

        reply_to_id = (
            serializer
            .validated_data
            .get(
                "reply_to_id"
            )
        )

        if reply_to_id:
            reply_to = get_object_or_404(
                Message.objects,
                id=reply_to_id,
                channel=channel,
            )

        try:
            message = create_message(
                channel=channel,
                author=request.user,
                content=(
                    serializer
                    .validated_data[
                        "content"
                    ]
                ),
                reply_to=reply_to,
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            MessageSerializer(
                message
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class MessageDetailView(
    WorkspaceChannelAccessMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_message(
        self,
    ):
        channel = (
            self.get_active_channel()
        )

        return get_object_or_404(
            Message.objects
            .select_related(
                "channel",
                "channel__workspace",
                "author",
                "reply_to",
                "reply_to__author",
            ),
            id=self.kwargs[
                "message_id"
            ],
            channel=channel,
            deleted_at__isnull=True,
        )

    def patch(
        self,
        request,
        workspace_slug,
        channel_id,
        message_id,
    ):
        message = (
            self.get_message()
        )

        serializer = (
            MessageUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            message = update_message(
                message=message,
                actor=request.user,
                content=(
                    serializer
                    .validated_data[
                        "content"
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
            MessageSerializer(
                message
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        channel_id,
        message_id,
    ):
        message = (
            self.get_message()
        )

        try:
            delete_message(
                message=message,
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