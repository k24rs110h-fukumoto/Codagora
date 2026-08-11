from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)

from workspaces.models import (
    WorkspaceMember,
)

from .models import WorkspaceFile


def get_workspace_role(
    *,
    workspace,
    user,
):
    if workspace.owner_id == user.id:
        return WorkspaceMember.Role.OWNER

    membership = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .first()
    )

    if membership is None:
        return None

    return membership.role


def require_workspace_file_viewer(
    *,
    workspace,
    user,
):
    role = get_workspace_role(
        workspace=workspace,
        user=user,
    )

    if role not in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
        WorkspaceMember.Role.MEMBER,
        WorkspaceMember.Role.GUEST,
    ):
        raise PermissionDenied(
            "このファイルを閲覧する"
            "権限がありません。"
        )

    return role


def get_workspace_file_for_download(
    *,
    file_id,
    user,
):
    workspace_file = (
        WorkspaceFile.objects
        .filter(
            id=file_id,
            deleted_at__isnull=True,
        )
        .select_related(
            "workspace",
            "folder",
            "uploaded_by",
        )
        .first()
    )

    if workspace_file is None:
        raise ValidationError(
            "ファイルが存在しません。"
        )

    require_workspace_file_viewer(
        workspace=workspace_file.workspace,
        user=user,
    )

    if not workspace_file.file:
        raise ValidationError(
            "ファイルデータが存在しません。"
        )

    storage = workspace_file.file.storage

    if not storage.exists(
        workspace_file.file.name
    ):
        raise ValidationError(
            "保存されたファイルが"
            "見つかりません。"
        )

    return workspace_file