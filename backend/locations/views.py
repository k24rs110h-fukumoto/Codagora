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
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from workspaces.selectors import (
    get_accessible_workspaces,
)

from .models import WorkspacePlace
from .selectors import (
    get_active_location_shares,
    get_current_location_share,
    get_workspace_places,
)
from .serializers import (
    WorkspaceLocationShareCreateSerializer,
    WorkspaceLocationShareSerializer,
    WorkspacePlaceSerializer,
    WorkspacePlaceUpdateSerializer,
    WorkspacePlaceWriteSerializer,
)
from .services import (
    create_workspace_place,
    delete_workspace_place,
    require_location_share_viewer,
    start_location_share,
    stop_location_share,
    update_workspace_place,
)


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
        if hasattr(
            error,
            "message_dict",
        ):
            raise ValidationError(
                error.message_dict
            ) from error

        raise ValidationError(
            {
                "detail": (
                    error.messages
                ),
            }
        ) from error

    raise error


class WorkspaceLocationMixin:
    def get_workspace(self):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=self.kwargs[
                "workspace_slug"
            ],
        )

    def get_place(self):
        return get_object_or_404(
            WorkspacePlace.objects
            .select_related(
                "workspace",
                "created_by",
            ),
            id=self.kwargs[
                "place_id"
            ],
            workspace=(
                self.get_workspace()
            ),
            deleted_at__isnull=True,
        )


class WorkspacePlaceListCreateView(
    WorkspaceLocationMixin,
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

        places = get_workspace_places(
            workspace=workspace,
        )

        return Response(
            WorkspacePlaceSerializer(
                places,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request,
        workspace_slug,
    ):
        serializer = (
            WorkspacePlaceWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            place = (
                create_workspace_place(
                    workspace=(
                        self.get_workspace()
                    ),
                    actor=request.user,
                    **serializer.validated_data,
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
            WorkspacePlaceSerializer(
                place
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspacePlaceDetailView(
    WorkspaceLocationMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        place_id,
    ):
        return Response(
            WorkspacePlaceSerializer(
                self.get_place()
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        workspace_slug,
        place_id,
    ):
        serializer = (
            WorkspacePlaceUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            place = (
                update_workspace_place(
                    place=(
                        self.get_place()
                    ),
                    actor=request.user,
                    changes=dict(
                        serializer
                        .validated_data
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
            WorkspacePlaceSerializer(
                place
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        place_id,
    ):
        try:
            delete_workspace_place(
                place=self.get_place(),
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


class WorkspaceLocationShareListView(
    WorkspaceLocationMixin,
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

        try:
            require_location_share_viewer(
                workspace=workspace,
                user=request.user,
            )

        except DjangoPermissionDenied as error:
            handle_service_error(
                error
            )

        shares = (
            get_active_location_shares(
                workspace=workspace,
            )
        )

        return Response(
            WorkspaceLocationShareSerializer(
                shares,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request,
        workspace_slug,
    ):
        serializer = (
            WorkspaceLocationShareCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            share = start_location_share(
                workspace=(
                    self.get_workspace()
                ),
                actor=request.user,
                **serializer.validated_data,
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            WorkspaceLocationShareSerializer(
                share
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class CurrentWorkspaceLocationShareView(
    WorkspaceLocationMixin,
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

        try:
            require_location_share_viewer(
                workspace=workspace,
                user=request.user,
            )

        except DjangoPermissionDenied as error:
            handle_service_error(
                error
            )

        share = (
            get_current_location_share(
                workspace=workspace,
                user=request.user,
            )
        )

        if not share:
            return Response(
                {
                    "sharing": False,
                    "share": None,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "sharing": True,
                "share": (
                    WorkspaceLocationShareSerializer(
                        share
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
    ):
        try:
            stop_location_share(
                workspace=(
                    self.get_workspace()
                ),
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