import hashlib
import mimetypes

from django.conf import settings
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import (
    IntegrityError,
    transaction,
)
from django.utils import timezone

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from activity.recorders import (
    record_file_uploaded,
)

from notifications.recorders import (
    notify_file_uploaded,
)

from .models import (
    WorkspaceFile,
    WorkspaceFolder,
)


def get_workspace_role(
    *,
    workspace,
    user,
):
    if workspace.owner_id == user.id:
        return (
            WorkspaceMember.Role.OWNER
        )

    membership = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .first()
    )

    if not membership:
        return None

    return membership.role


def is_workspace_manager(
    *,
    workspace,
    user,
):
    return (
        get_workspace_role(
            workspace=workspace,
            user=user,
        )
        in (
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        )
    )


def require_workspace_contributor(
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
    ):
        raise PermissionDenied(
            "この操作にはMember以上の"
            "権限が必要です。"
        )

    return role


def normalize_entry_name(
    name,
):
    normalized = name.strip()

    if not normalized:
        raise ValidationError(
            "名前を入力してください。"
        )

    if normalized in (
        ".",
        "..",
    ):
        raise ValidationError(
            "この名前は使用できません。"
        )

    if (
        "/"
        in normalized
        or "\\"
        in normalized
        or "\x00"
        in normalized
    ):
        raise ValidationError(
            "名前に使用できない"
            "文字が含まれています。"
        )

    if len(normalized) > 255:
        raise ValidationError(
            "名前は255文字以内で"
            "入力してください。"
        )

    return normalized


def safe_original_filename(
    filename,
):
    normalized = (
        filename
        .replace("\\", "/")
        .split("/")[-1]
    )

    return normalize_entry_name(
        normalized
    )


def get_locked_workspace(
    workspace,
):
    return (
        Workspace.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace.id,
        )
    )


def get_active_folder(
    *,
    workspace,
    folder_id,
):
    if folder_id is None:
        return None

    folder = (
        WorkspaceFolder.objects
        .filter(
            id=folder_id,
            workspace=workspace,
            deleted_at__isnull=True,
        )
        .first()
    )

    if not folder:
        raise ValidationError(
            "指定したフォルダが"
            "存在しません。"
        )

    return folder


def active_name_exists(
    *,
    workspace,
    folder,
    name,
    exclude_folder_id=None,
    exclude_file_id=None,
):
    folder_queryset = (
        WorkspaceFolder.objects
        .filter(
            workspace=workspace,
            parent=folder,
            name__iexact=name,
            deleted_at__isnull=True,
        )
    )

    if exclude_folder_id:
        folder_queryset = (
            folder_queryset.exclude(
                id=exclude_folder_id,
            )
        )

    if folder_queryset.exists():
        return True

    file_queryset = (
        WorkspaceFile.objects
        .filter(
            workspace=workspace,
            folder=folder,
            display_name__iexact=name,
            deleted_at__isnull=True,
        )
    )

    if exclude_file_id:
        file_queryset = (
            file_queryset.exclude(
                id=exclude_file_id,
            )
        )

    return file_queryset.exists()


def can_manage_folder(
    *,
    folder,
    user,
):
    role = get_workspace_role(
        workspace=folder.workspace,
        user=user,
    )

    if role not in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
        WorkspaceMember.Role.MEMBER,
    ):
        return False

    return (
        role in (
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        )
        or folder.created_by_id
        == user.id
    )


def can_manage_file(
    *,
    workspace_file,
    user,
):
    role = get_workspace_role(
        workspace=workspace_file.workspace,
        user=user,
    )

    if role not in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
        WorkspaceMember.Role.MEMBER,
    ):
        return False

    return (
        role in (
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        )
        or workspace_file.uploaded_by_id
        == user.id
    )


def calculate_sha256(
    uploaded_file,
):
    digest = hashlib.sha256()

    for chunk in (
        uploaded_file.chunks()
    ):
        digest.update(chunk)

    uploaded_file.seek(0)

    return digest.hexdigest()


def validate_folder_move(
    *,
    folder,
    parent,
):
    if parent is None:
        return

    if parent.id == folder.id:
        raise ValidationError(
            "フォルダ自身を親には"
            "指定できません。"
        )

    current = parent

    while current is not None:
        if current.id == folder.id:
            raise ValidationError(
                "フォルダを自身の"
                "子孫へ移動できません。"
            )

        if current.parent_id is None:
            break

        current = (
            WorkspaceFolder.objects
            .filter(
                id=current.parent_id,
                workspace=(
                    folder.workspace
                ),
                deleted_at__isnull=True,
            )
            .first()
        )


@transaction.atomic
def create_workspace_folder(
    *,
    workspace,
    actor,
    name,
    parent_id=None,
):
    workspace = (
        get_locked_workspace(
            workspace
        )
    )

    require_workspace_contributor(
        workspace=workspace,
        user=actor,
    )

    parent = get_active_folder(
        workspace=workspace,
        folder_id=parent_id,
    )

    normalized_name = (
        normalize_entry_name(
            name
        )
    )

    if active_name_exists(
        workspace=workspace,
        folder=parent,
        name=normalized_name,
    ):
        raise ValidationError(
            "同じ場所に同名の"
            "ファイルまたはフォルダが"
            "存在します。"
        )

    try:
        return (
            WorkspaceFolder.objects
            .create(
                workspace=workspace,
                name=normalized_name,
                parent=parent,
                created_by=actor,
            )
        )

    except IntegrityError as error:
        raise ValidationError(
            "同名フォルダが"
            "すでに存在します。"
        ) from error


@transaction.atomic
def update_workspace_folder(
    *,
    folder,
    actor,
    changes,
):
    folder = (
        WorkspaceFolder.objects
        .select_related(
            "workspace",
            "parent",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=folder.id,
            deleted_at__isnull=True,
        )
    )

    if not can_manage_folder(
        folder=folder,
        user=actor,
    ):
        raise PermissionDenied(
            "このフォルダを"
            "変更する権限がありません。"
        )

    new_name = folder.name
    new_parent = folder.parent

    if "name" in changes:
        new_name = normalize_entry_name(
            changes["name"]
        )

    if "parent_id" in changes:
        new_parent = get_active_folder(
            workspace=folder.workspace,
            folder_id=(
                changes[
                    "parent_id"
                ]
            ),
        )

        validate_folder_move(
            folder=folder,
            parent=new_parent,
        )

    if active_name_exists(
        workspace=folder.workspace,
        folder=new_parent,
        name=new_name,
        exclude_folder_id=folder.id,
    ):
        raise ValidationError(
            "移動先に同名の"
            "ファイルまたはフォルダが"
            "存在します。"
        )

    folder.name = new_name
    folder.parent = new_parent

    try:
        folder.save(
            update_fields=(
                "name",
                "parent",
                "updated_at",
            )
        )

    except IntegrityError as error:
        raise ValidationError(
            "同名フォルダが"
            "すでに存在します。"
        ) from error

    return folder


@transaction.atomic
def delete_workspace_folder(
    *,
    folder,
    actor,
):
    folder = (
        WorkspaceFolder.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=folder.id,
            deleted_at__isnull=True,
        )
    )

    if not can_manage_folder(
        folder=folder,
        user=actor,
    ):
        raise PermissionDenied(
            "このフォルダを"
            "削除する権限がありません。"
        )

    has_folders = (
        WorkspaceFolder.objects
        .filter(
            parent=folder,
            deleted_at__isnull=True,
        )
        .exists()
    )

    has_files = (
        WorkspaceFile.objects
        .filter(
            folder=folder,
            deleted_at__isnull=True,
        )
        .exists()
    )

    if has_folders or has_files:
        raise ValidationError(
            "フォルダが空ではありません。"
            "中身を移動または削除してから"
            "削除してください。"
        )

    folder.deleted_at = (
        timezone.now()
    )

    folder.deleted_by = actor

    folder.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return folder


@transaction.atomic
def restore_workspace_folder(
    *,
    folder,
    actor,
):
    folder = (
        WorkspaceFolder.objects
        .select_related(
            "workspace",
            "parent",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=folder.id,
            deleted_at__isnull=False,
        )
    )

    if not can_manage_folder(
        folder=folder,
        user=actor,
    ):
        raise PermissionDenied(
            "このフォルダを"
            "復元する権限がありません。"
        )

    if (
        folder.parent
        and folder.parent.deleted_at
    ):
        raise ValidationError(
            "親フォルダが削除されています。"
            "先に親フォルダを"
            "復元してください。"
        )

    if active_name_exists(
        workspace=folder.workspace,
        folder=folder.parent,
        name=folder.name,
        exclude_folder_id=folder.id,
    ):
        raise ValidationError(
            "復元先に同名の"
            "ファイルまたはフォルダが"
            "存在します。"
        )

    folder.deleted_at = None
    folder.deleted_by = None

    folder.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return folder


@transaction.atomic
def upload_workspace_file(
    *,
    workspace,
    actor,
    uploaded_file,
    folder_id=None,
    display_name=None,
):
    workspace = (
        get_locked_workspace(
            workspace
        )
    )

    require_workspace_contributor(
        workspace=workspace,
        user=actor,
    )

    maximum = (
        settings
        .WORKSPACE_FILE_MAX_UPLOAD_SIZE_BYTES
    )

    if uploaded_file.size > maximum:
        raise ValidationError(
            "ファイルサイズが"
            "上限を超えています。"
        )

    folder = get_active_folder(
        workspace=workspace,
        folder_id=folder_id,
    )

    original_name = (
        safe_original_filename(
            uploaded_file.name
        )
    )

    normalized_display_name = (
        normalize_entry_name(
            display_name
            or original_name
        )
    )

    if active_name_exists(
        workspace=workspace,
        folder=folder,
        name=normalized_display_name,
    ):
        raise ValidationError(
            "同じ場所に同名の"
            "ファイルまたはフォルダが"
            "存在します。"
        )

    sha256 = calculate_sha256(
        uploaded_file
    )

    content_type = (
        getattr(
            uploaded_file,
            "content_type",
            "",
        )
        or mimetypes.guess_type(
            original_name
        )[0]
        or "application/octet-stream"
    )

    workspace_file = WorkspaceFile(
        workspace=workspace,
        folder=folder,
        original_name=original_name,
        display_name=(
            normalized_display_name
        ),
        content_type=content_type,
        size_bytes=(
            uploaded_file.size
        ),
        sha256=sha256,
        uploaded_by=actor,
    )

    try:
        workspace_file.file = (
            uploaded_file
        )

        workspace_file.save()

    except IntegrityError as error:
        if workspace_file.file:
            workspace_file.file.delete(
                save=False
            )

        raise ValidationError(
            "同名ファイルが"
            "すでに存在します。"
        ) from error

    record_file_uploaded(
        workspace=workspace,
        actor=actor,
        file_id=workspace_file.id,
        file_name=workspace_file.display_name,
        size_bytes=workspace_file.size_bytes,
    )

    notify_file_uploaded(
        workspace=workspace,
        actor=actor,
        workspace_file=workspace_file,
    )

    return workspace_file


@transaction.atomic
def update_workspace_file(
    *,
    workspace_file,
    actor,
    changes,
):
    workspace_file = (
        WorkspaceFile.objects
        .select_related(
            "workspace",
            "folder",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace_file.id,
            deleted_at__isnull=True,
        )
    )

    if not can_manage_file(
        workspace_file=workspace_file,
        user=actor,
    ):
        raise PermissionDenied(
            "このファイルを"
            "変更する権限がありません。"
        )

    new_name = (
        workspace_file.display_name
    )

    new_folder = (
        workspace_file.folder
    )

    if "display_name" in changes:
        new_name = normalize_entry_name(
            changes[
                "display_name"
            ]
        )

    if "folder_id" in changes:
        new_folder = get_active_folder(
            workspace=(
                workspace_file.workspace
            ),
            folder_id=(
                changes["folder_id"]
            ),
        )

    if active_name_exists(
        workspace=(
            workspace_file.workspace
        ),
        folder=new_folder,
        name=new_name,
        exclude_file_id=(
            workspace_file.id
        ),
    ):
        raise ValidationError(
            "移動先に同名の"
            "ファイルまたはフォルダが"
            "存在します。"
        )

    workspace_file.display_name = (
        new_name
    )

    workspace_file.folder = (
        new_folder
    )

    try:
        workspace_file.save(
            update_fields=(
                "display_name",
                "folder",
                "updated_at",
            )
        )

    except IntegrityError as error:
        raise ValidationError(
            "同名ファイルが"
            "すでに存在します。"
        ) from error

    return workspace_file


@transaction.atomic
def delete_workspace_file(
    *,
    workspace_file,
    actor,
):
    workspace_file = (
        WorkspaceFile.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace_file.id,
        )
    )

    if workspace_file.deleted_at:
        return workspace_file

    if not can_manage_file(
        workspace_file=workspace_file,
        user=actor,
    ):
        raise PermissionDenied(
            "このファイルを"
            "削除する権限がありません。"
        )

    workspace_file.deleted_at = (
        timezone.now()
    )

    workspace_file.deleted_by = actor

    workspace_file.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return workspace_file


@transaction.atomic
def restore_workspace_file(
    *,
    workspace_file,
    actor,
):
    workspace_file = (
        WorkspaceFile.objects
        .select_related(
            "workspace",
            "folder",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace_file.id,
            deleted_at__isnull=False,
        )
    )

    if not can_manage_file(
        workspace_file=workspace_file,
        user=actor,
    ):
        raise PermissionDenied(
            "このファイルを"
            "復元する権限がありません。"
        )

    if (
        workspace_file.folder
        and workspace_file
        .folder
        .deleted_at
    ):
        raise ValidationError(
            "保存先フォルダが"
            "削除されています。"
            "先にフォルダを"
            "復元してください。"
        )

    if active_name_exists(
        workspace=(
            workspace_file.workspace
        ),
        folder=(
            workspace_file.folder
        ),
        name=(
            workspace_file
            .display_name
        ),
        exclude_file_id=(
            workspace_file.id
        ),
    ):
        raise ValidationError(
            "復元先に同名の"
            "ファイルまたはフォルダが"
            "存在します。"
        )

    workspace_file.deleted_at = None
    workspace_file.deleted_by = None

    workspace_file.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return workspace_file