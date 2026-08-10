from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
)
from rest_framework.generics import (
    ListAPIView,
)
from rest_framework.response import (
    Response,
)
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)

from .models import Notification
from .pagination import (
    NotificationPagination,
)
from .selectors import (
    get_unread_notification_count,
    get_user_notifications,
)
from .serializers import (
    NotificationSerializer,
)
from .services import (
    mark_all_notifications_as_read,
    mark_notification_as_read,
    mark_notification_as_unread,
)


def validate_category(
    category,
):
    if (
        category
        and category
        not in Notification.Category.values
    ):
        raise ValidationError(
            {
                "category": (
                    "Invalid notification category."
                )
            }
        )

    return category


class NotificationListView(
    ListAPIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    serializer_class = (
        NotificationSerializer
    )

    pagination_class = (
        NotificationPagination
    )

    def get_queryset(self):
        category = validate_category(
            self.request.query_params.get(
                "category"
            )
        )

        workspace_slug = (
            self.request.query_params.get(
                "workspace"
            )
        )

        unread_value = (
            self.request.query_params.get(
                "unread"
            )
        )

        unread_only = (
            unread_value
            in (
                "1",
                "true",
                "True",
            )
        )

        return get_user_notifications(
            user=self.request.user,
            category=category,
            unread_only=unread_only,
            workspace_slug=(
                workspace_slug
            ),
        )


class UnreadNotificationCountView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        count = (
            get_unread_notification_count(
                user=request.user,
            )
        )

        return Response(
            {
                "count": count,
            },
            status=status.HTTP_200_OK,
        )


class MarkNotificationReadView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        notification_id,
    ):
        notification = (
            get_object_or_404(
                Notification,
                id=notification_id,
                recipient=request.user,
            )
        )

        notification = (
            mark_notification_as_read(
                notification=(
                    notification
                ),
                user=request.user,
            )
        )

        serializer = (
            NotificationSerializer(
                notification
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class MarkNotificationUnreadView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        notification_id,
    ):
        notification = (
            get_object_or_404(
                Notification,
                id=notification_id,
                recipient=request.user,
            )
        )

        notification = (
            mark_notification_as_unread(
                notification=(
                    notification
                ),
                user=request.user,
            )
        )

        serializer = (
            NotificationSerializer(
                notification
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class MarkAllNotificationsReadView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
    ):
        updated_count = (
            mark_all_notifications_as_read(
                user=request.user,
            )
        )

        return Response(
            {
                "updated_count": (
                    updated_count
                ),
            },
            status=status.HTTP_200_OK,
        )