from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import status
from rest_framework.exceptions import (
    PermissionDenied,
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
from workspaces.models import (
    Workspace,
)

from .models import ActivityEvent
from .overview import (
    build_activity_overview,
)
from .pagination import (
    ActivityPagination,
)
from .selectors import (
    get_personal_activity_events,
    get_workspace_activity_events,
    get_workspace_role,
)
from .serializers import (
    ActivityEventSerializer,
    ActivityOverviewSerializer,
)


def validate_category(
    category,
):
    if (
        category
        and category
        not in ActivityEvent.Category.values
    ):
        raise ValidationError(
            {
                "category": (
                    "Invalid activity category."
                )
            }
        )

    return category


class ActivityOverviewView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        payload = (
            build_activity_overview(
                user=request.user,
            )
        )

        serializer = (
            ActivityOverviewSerializer(
                payload
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class PersonalActivityListView(
    ListAPIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    serializer_class = (
        ActivityEventSerializer
    )

    pagination_class = (
        ActivityPagination
    )

    def get_queryset(self):
        category = (
            validate_category(
                self.request
                .query_params
                .get(
                    "category"
                )
            )
        )

        workspace_slug = (
            self.request
            .query_params
            .get(
                "workspace"
            )
        )

        return (
            get_personal_activity_events(
                user=self.request.user,
                category=category,
                workspace_slug=(
                    workspace_slug
                ),
            )
        )


class WorkspaceActivityListView(
    ListAPIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    serializer_class = (
        ActivityEventSerializer
    )

    pagination_class = (
        ActivityPagination
    )

    def get_queryset(self):
        workspace = (
            get_object_or_404(
                Workspace,
                slug=(
                    self.kwargs[
                        "workspace_slug"
                    ]
                ),
            )
        )

        role = get_workspace_role(
            workspace=workspace,
            user=self.request.user,
        )

        if role is None:
            raise PermissionDenied(
                "You are not a member "
                "of this workspace."
            )

        category = (
            validate_category(
                self.request
                .query_params
                .get(
                    "category"
                )
            )
        )

        return (
            get_workspace_activity_events(
                workspace=workspace,
                viewer=self.request.user,
                category=category,
            )
        )