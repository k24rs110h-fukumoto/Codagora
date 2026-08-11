from datetime import timedelta

from django.conf import settings
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import transaction
from django.utils import timezone

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from activity.recorders import (
    record_place_created,
)

from .models import (
    WorkspaceLocationShare,
    WorkspacePlace,
)


def get_workspace_role(
    *,
    workspace,
    user,
):
    if (
        workspace.owner_id
        == user.id
    ):
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


def require_location_share_viewer(
    *,
    workspace,
    user,
):
    return require_workspace_contributor(
        workspace=workspace,
        user=user,
    )


def is_workspace_manager(
    *,
    workspace,
    user,
):
    role = get_workspace_role(
        workspace=workspace,
        user=user,
    )

    return role in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
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


def can_manage_place(
    *,
    place,
    user,
):
    role = get_workspace_role(
        workspace=place.workspace,
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
        or place.created_by_id
        == user.id
    )


@transaction.atomic
def create_workspace_place(
    *,
    workspace,
    actor,
    name,
    description,
    address,
    latitude,
    longitude,
):
    workspace = get_locked_workspace(
        workspace
    )

    require_workspace_contributor(
        workspace=workspace,
        user=actor,
    )

    normalized_name = name.strip()

    if not normalized_name:
        raise ValidationError(
            "地点名を入力してください。"
        )

    place = WorkspacePlace.objects.create(
        workspace=workspace,
        name=normalized_name,
        description=description.strip(),
        address=address.strip(),
        latitude=latitude,
        longitude=longitude,
        created_by=actor,
    )

    record_place_created(
        workspace=workspace,
        actor=actor,
        place=place,
    )

    return place


@transaction.atomic
def update_workspace_place(
    *,
    place,
    actor,
    changes,
):
    place = (
        WorkspacePlace.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=place.id,
            deleted_at__isnull=True,
        )
    )

    if not can_manage_place(
        place=place,
        user=actor,
    ):
        raise PermissionDenied(
            "この地点を変更する"
            "権限がありません。"
        )

    if "name" in changes:
        name = changes[
            "name"
        ].strip()

        if not name:
            raise ValidationError(
                "地点名を入力してください。"
            )

        place.name = name

    if "description" in changes:
        place.description = (
            changes[
                "description"
            ].strip()
        )

    if "address" in changes:
        place.address = (
            changes[
                "address"
            ].strip()
        )

    if "latitude" in changes:
        place.latitude = (
            changes["latitude"]
        )

    if "longitude" in changes:
        place.longitude = (
            changes["longitude"]
        )

    place.save()

    return place


@transaction.atomic
def delete_workspace_place(
    *,
    place,
    actor,
):
    place = (
        WorkspacePlace.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=place.id,
            deleted_at__isnull=True,
        )
    )

    if not can_manage_place(
        place=place,
        user=actor,
    ):
        raise PermissionDenied(
            "この地点を削除する"
            "権限がありません。"
        )

    place.deleted_at = timezone.now()
    place.deleted_by = actor

    place.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return place


@transaction.atomic
def start_location_share(
    *,
    workspace,
    actor,
    place_id=None,
    label="",
    note="",
    latitude=None,
    longitude=None,
    accuracy_meters=None,
    duration_minutes=None,
):
    workspace = get_locked_workspace(
        workspace
    )

    require_workspace_contributor(
        workspace=workspace,
        user=actor,
    )

    if duration_minutes is None:
        duration_minutes = (
            settings
            .LOCATION_SHARE_DEFAULT_DURATION_MINUTES
        )

    maximum = (
        settings
        .LOCATION_SHARE_MAX_DURATION_MINUTES
    )

    if not (
        15
        <= duration_minutes
        <= maximum
    ):
        raise ValidationError(
            f"位置共有時間は15〜"
            f"{maximum}分で指定してください。"
        )

    place = None

    if place_id:
        place = (
            WorkspacePlace.objects
            .filter(
                id=place_id,
                workspace=workspace,
                deleted_at__isnull=True,
            )
            .first()
        )

        if not place:
            raise ValidationError(
                "指定した保存地点が"
                "存在しません。"
            )

        if latitude is None:
            latitude = place.latitude

        if longitude is None:
            longitude = (
                place.longitude
            )

        if not label:
            label = place.name

    if (
        latitude is None
        or longitude is None
    ):
        raise ValidationError(
            "位置情報がありません。"
        )

    now = timezone.now()

    (
        WorkspaceLocationShare.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=workspace,
            user=actor,
            ended_at__isnull=True,
        )
        .update(
            ended_at=now,
            updated_at=now,
        )
    )

    return (
        WorkspaceLocationShare.objects
        .create(
            workspace=workspace,
            user=actor,
            place=place,
            label=label.strip(),
            note=note.strip(),
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=(
                accuracy_meters
            ),
            expires_at=(
                now
                + timedelta(
                    minutes=duration_minutes
                )
            ),
        )
    )


@transaction.atomic
def stop_location_share(
    *,
    workspace,
    actor,
):
    workspace = get_locked_workspace(
        workspace
    )

    require_workspace_contributor(
        workspace=workspace,
        user=actor,
    )

    share = (
        WorkspaceLocationShare.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=workspace,
            user=actor,
            ended_at__isnull=True,
        )
        .order_by(
            "-started_at"
        )
        .first()
    )

    if not share:
        raise ValidationError(
            "現在共有中の位置情報は"
            "ありません。"
        )

    share.ended_at = timezone.now()

    share.save(
        update_fields=(
            "ended_at",
            "updated_at",
        )
    )

    return share