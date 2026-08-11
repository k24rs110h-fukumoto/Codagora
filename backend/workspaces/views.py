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
    generics,
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

from .permissions import (
    IsWorkspaceOwnerOrAdmin,
)
from .selectors import (
    get_accessible_workspaces,
    get_active_workspace_members,
    get_workspace_invitations,
)
from .serializers import (
    WorkspaceInvitationAcceptSerializer,
    WorkspaceInvitationCreateSerializer,
    WorkspaceInvitationCreatedSerializer,
    WorkspaceInvitationReissueSerializer,
    WorkspaceInvitationSerializer,
    WorkspaceMemberRoleUpdateSerializer,
    WorkspaceMemberSerializer,
    WorkspaceMembershipSerializer,
    WorkspaceOwnershipTransferSerializer,
    WorkspaceSerializer,
    WorkspaceWriteSerializer,
)
from .services import (
    accept_workspace_invitation,
    change_workspace_member_role,
    create_workspace,
    create_workspace_invitation,
    delete_workspace,
    leave_workspace,
    reissue_workspace_invitation,
    remove_workspace_member,
    revoke_workspace_invitation,
    transfer_workspace_ownership,
    update_workspace,
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


class WorkspaceListCreateView(
    generics.ListAPIView,
):
    serializer_class = (
        WorkspaceSerializer
    )

    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_queryset(self):
        return (
            get_accessible_workspaces(
                user=self.request.user,
            )
        )

    def post(
        self,
        request,
    ):
        serializer = (
            WorkspaceWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            workspace = (
                create_workspace(
                    owner=request.user,
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
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        output = WorkspaceSerializer(
            workspace,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspaceDetailView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_workspace(
        self,
        request,
        slug,
    ):
        return get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

    def get(
        self,
        request,
        slug,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        serializer = WorkspaceSerializer(
            workspace,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
        )

    def patch(
        self,
        request,
        slug,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        initial = {
            "name": workspace.name,
            "description": (
                workspace.description
            ),
        }

        initial.update(
            request.data
        )

        serializer = (
            WorkspaceWriteSerializer(
                data=initial,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            workspace = (
                update_workspace(
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
                        .validated_data[
                            "description"
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

        output = WorkspaceSerializer(
            workspace,
            context={
                "request": request,
            },
        )

        return Response(
            output.data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        slug,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        try:
            delete_workspace(
                workspace=workspace,
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


class WorkspaceMemberListView(
    generics.ListAPIView,
):
    serializer_class = (
        WorkspaceMemberSerializer
    )

    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_workspace(self):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=self.kwargs["slug"],
        )

    def get_queryset(self):
        workspace = (
            self.get_workspace()
        )

        return (
            get_active_workspace_members(
                workspace=workspace,
            )
        )


class WorkspaceMemberDetailView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_workspace(
        self,
        request,
        slug,
    ):
        return get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

    def patch(
        self,
        request,
        slug,
        membership_id,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        serializer = (
            WorkspaceMemberRoleUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            membership = (
                change_workspace_member_role(
                    workspace=workspace,
                    actor=request.user,
                    membership_id=(
                        membership_id
                    ),
                    new_role=(
                        serializer
                        .validated_data[
                            "role"
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
            WorkspaceMemberSerializer(
                membership
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        slug,
        membership_id,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        try:
            remove_workspace_member(
                workspace=workspace,
                actor=request.user,
                membership_id=(
                    membership_id
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
            status=(
                status.HTTP_204_NO_CONTENT
            ),
        )


class WorkspaceLeaveView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        slug,
    ):
        workspace = get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

        try:
            leave_workspace(
                workspace=workspace,
                user=request.user,
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
            ),
        )


class WorkspaceOwnershipTransferView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    throttle_scope = (
        "auth_sensitive"
    )

    def post(
        self,
        request,
        slug,
    ):
        workspace = get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

        serializer = (
            WorkspaceOwnershipTransferSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            workspace = (
                transfer_workspace_ownership(
                    workspace=workspace,
                    current_owner=(
                        request.user
                    ),
                    target_membership_id=(
                        serializer
                        .validated_data[
                            "membership_id"
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
            WorkspaceSerializer(
                workspace,
                context={
                    "request": request,
                },
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceInvitationCreateView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
        IsWorkspaceOwnerOrAdmin,
    )

    def get_workspace(
        self,
        request,
        slug,
    ):
        workspace = get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

        self.check_object_permissions(
            request,
            workspace,
        )

        return workspace

    def get(
        self,
        request,
        slug,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        invitations = (
            get_workspace_invitations(
                workspace=workspace,
            )
        )

        return Response(
            WorkspaceInvitationSerializer(
                invitations,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request,
        slug,
    ):
        workspace = self.get_workspace(
            request,
            slug,
        )

        serializer = (
            WorkspaceInvitationCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            invitation, token = (
                create_workspace_invitation(
                    workspace=workspace,
                    created_by=(
                        request.user
                    ),
                    role=(
                        serializer
                        .validated_data[
                            "role"
                        ]
                    ),
                    expires_in_days=(
                        serializer
                        .validated_data[
                            "expires_in_days"
                        ]
                    ),
                    max_uses=(
                        serializer
                        .validated_data[
                            "max_uses"
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

        output = (
            WorkspaceInvitationCreatedSerializer(
                {
                    "id": invitation.id,
                    "workspace": (
                        invitation.workspace
                    ),
                    "role": (
                        invitation.role
                    ),
                    "expires_at": (
                        invitation.expires_at
                    ),
                    "max_uses": (
                        invitation.max_uses
                    ),
                    "use_count": (
                        invitation.use_count
                    ),
                    "is_active": (
                        invitation.is_active
                    ),
                    "token": token,
                }
            )
        )

        return Response(
            output.data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspaceInvitationRevokeView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        slug,
        invitation_id,
    ):
        workspace = get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

        try:
            invitation = (
                revoke_workspace_invitation(
                    workspace=workspace,
                    actor=request.user,
                    invitation_id=(
                        invitation_id
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
            WorkspaceInvitationSerializer(
                invitation
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceInvitationReissueView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        slug,
        invitation_id,
    ):
        workspace = get_object_or_404(
            get_accessible_workspaces(
                user=request.user,
            ),
            slug=slug,
        )

        serializer = (
            WorkspaceInvitationReissueSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            invitation, token = (
                reissue_workspace_invitation(
                    workspace=workspace,
                    actor=request.user,
                    invitation_id=(
                        invitation_id
                    ),
                    expires_in_days=(
                        serializer
                        .validated_data[
                            "expires_in_days"
                        ]
                    ),
                    max_uses=(
                        serializer
                        .validated_data
                        .get(
                            "max_uses"
                        )
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

        output = (
            WorkspaceInvitationCreatedSerializer(
                {
                    "id": invitation.id,
                    "workspace": (
                        invitation.workspace
                    ),
                    "role": (
                        invitation.role
                    ),
                    "expires_at": (
                        invitation.expires_at
                    ),
                    "max_uses": (
                        invitation.max_uses
                    ),
                    "use_count": (
                        invitation.use_count
                    ),
                    "is_active": (
                        invitation.is_active
                    ),
                    "token": token,
                }
            )
        )

        return Response(
            output.data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspaceInvitationAcceptView(
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
    ):
        serializer = (
            WorkspaceInvitationAcceptSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            membership = (
                accept_workspace_invitation(
                    user=request.user,
                    token=(
                        serializer
                        .validated_data[
                            "token"
                        ]
                    ),
                )
            )

        except DjangoValidationError as error:
            raise_drf_validation_error(
                error
            )

        return Response(
            WorkspaceMembershipSerializer(
                membership
            ).data,
            status=status.HTTP_200_OK,
        )