from rest_framework.permissions import (
    BasePermission,
)

from .models import (
    Workspace,
    WorkspaceMember,
)


class IsWorkspaceOwner(
    BasePermission,
):
    message = (
        "Workspace Ownerのみ実行できます。"
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if not isinstance(
            obj,
            Workspace,
        ):
            return False

        return (
            obj.owner_id
            == request.user.id
        )


class IsWorkspaceOwnerOrAdmin(
    BasePermission,
):
    message = (
        "Workspace OwnerまたはAdmin"
        "のみ実行できます。"
    )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if not isinstance(
            obj,
            Workspace,
        ):
            return False

        if (
            obj.owner_id
            == request.user.id
        ):
            return True

        return (
            WorkspaceMember.objects
            .filter(
                workspace=obj,
                user=request.user,
                role=(
                    WorkspaceMember
                    .Role
                    .ADMIN
                ),
                is_active=True,
            )
            .exists()
        )