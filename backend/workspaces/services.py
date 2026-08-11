import hashlib
import secrets
import uuid

from datetime import timedelta

from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
)

from activity.recorders import (
    record_workspace_created,
    record_workspace_member_joined,
)

from notifications.recorders import (
    notify_workspace_member_joined,
)


def generate_workspace_slug(
    name,
):
    base = (
        slugify(
            name,
            allow_unicode=True,
        )
        .strip("-")
    )

    if not base:
        base = "workspace"

    base = base[:100]

    while True:
        suffix = uuid.uuid4().hex[:8]

        slug = (
            f"{base}-{suffix}"
        )

        if not Workspace.objects.filter(
            slug=slug
        ).exists():
            return slug


def hash_invitation_token(
    token,
):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _get_locked_workspace(
    workspace,
):
    workspace_id = (
        workspace.id
        if isinstance(
            workspace,
            Workspace,
        )
        else workspace
    )

    return (
        Workspace.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace_id,
        )
    )


def _get_locked_membership(
    *,
    workspace,
    user,
):
    return (
        WorkspaceMember.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .first()
    )


def _get_actor_role(
    *,
    workspace,
    actor,
):
    if (
        workspace.owner_id
        == actor.id
    ):
        return (
            WorkspaceMember.Role.OWNER
        )

    membership = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=actor,
            is_active=True,
        )
        .first()
    )

    if not membership:
        return None

    return membership.role


def _require_manager(
    *,
    workspace,
    actor,
):
    role = _get_actor_role(
        workspace=workspace,
        actor=actor,
    )

    if role not in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
    ):
        raise PermissionDenied(
            "Workspace管理権限がありません。"
        )

    return role


@transaction.atomic
def create_workspace(
    *,
    owner,
    name,
    description="",
):
    normalized_name = name.strip()

    if not normalized_name:
        raise ValidationError(
            "Workspace名を入力してください。"
        )

    workspace = Workspace.objects.create(
        name=normalized_name,
        slug=generate_workspace_slug(
            normalized_name
        ),
        description=(
            description.strip()
        ),
        owner=owner,
    )

    record_workspace_created(
        workspace=workspace,
        actor=owner,
    )

    WorkspaceMember.objects.create(
        workspace=workspace,
        user=owner,
        role=(
            WorkspaceMember.Role.OWNER
        ),
        is_active=True,
    )

    return workspace


@transaction.atomic
def update_workspace(
    *,
    workspace,
    actor,
    name,
    description,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    _require_manager(
        workspace=locked_workspace,
        actor=actor,
    )

    normalized_name = name.strip()

    if not normalized_name:
        raise ValidationError(
            "Workspace名を入力してください。"
        )

    locked_workspace.name = (
        normalized_name
    )

    locked_workspace.description = (
        description.strip()
    )

    locked_workspace.save(
        update_fields=(
            "name",
            "description",
            "updated_at",
        )
    )

    return locked_workspace


@transaction.atomic
def delete_workspace(
    *,
    workspace,
    actor,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    if (
        locked_workspace.owner_id
        != actor.id
    ):
        raise PermissionDenied(
            "Workspaceを削除できるのは"
            "Ownerのみです。"
        )

    locked_workspace.delete()


@transaction.atomic
def change_workspace_member_role(
    *,
    workspace,
    actor,
    membership_id,
    new_role,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    actor_role = _require_manager(
        workspace=locked_workspace,
        actor=actor,
    )

    if new_role == (
        WorkspaceMember.Role.OWNER
    ):
        raise ValidationError(
            "Ownerへの変更は"
            "Owner移譲APIを使用してください。"
        )

    if new_role not in (
        WorkspaceMember.Role.ADMIN,
        WorkspaceMember.Role.MEMBER,
        WorkspaceMember.Role.GUEST,
    ):
        raise ValidationError(
            "Roleが不正です。"
        )

    membership = (
        WorkspaceMember.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=membership_id,
            workspace=locked_workspace,
            is_active=True,
        )
        .first()
    )

    if not membership:
        raise ValidationError(
            "対象メンバーが存在しません。"
        )

    if (
        membership.user_id
        == locked_workspace.owner_id
    ):
        raise ValidationError(
            "OwnerのRoleは"
            "直接変更できません。"
        )

    if (
        actor_role
        == WorkspaceMember.Role.ADMIN
    ):
        if (
            membership.role
            == WorkspaceMember.Role.ADMIN
            and membership.user_id
            != actor.id
        ):
            raise PermissionDenied(
                "Adminは別のAdminのRoleを"
                "変更できません。"
            )

        if (
            new_role
            == WorkspaceMember.Role.ADMIN
        ):
            raise PermissionDenied(
                "Adminへの昇格は"
                "Ownerのみ実行できます。"
            )

    membership.role = new_role

    membership.save(
        update_fields=(
            "role",
            "updated_at",
        )
    )

    return membership


@transaction.atomic
def remove_workspace_member(
    *,
    workspace,
    actor,
    membership_id,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    actor_role = _require_manager(
        workspace=locked_workspace,
        actor=actor,
    )

    membership = (
        WorkspaceMember.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=membership_id,
            workspace=locked_workspace,
            is_active=True,
        )
        .first()
    )

    if not membership:
        raise ValidationError(
            "対象メンバーが存在しません。"
        )

    if (
        membership.user_id
        == locked_workspace.owner_id
    ):
        raise ValidationError(
            "OwnerをWorkspaceから"
            "削除できません。"
        )

    if (
        membership.user_id
        == actor.id
    ):
        raise ValidationError(
            "自分自身の退出には"
            "退出APIを使用してください。"
        )

    if (
        actor_role
        == WorkspaceMember.Role.ADMIN
        and membership.role
        == WorkspaceMember.Role.ADMIN
    ):
        raise PermissionDenied(
            "Adminは別のAdminを"
            "削除できません。"
        )

    membership.is_active = False
    membership.left_at = timezone.now()

    membership.save(
        update_fields=(
            "is_active",
            "left_at",
            "updated_at",
        )
    )

    return membership


@transaction.atomic
def leave_workspace(
    *,
    workspace,
    user,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    if (
        locked_workspace.owner_id
        == user.id
    ):
        raise ValidationError(
            "Ownerはそのまま"
            "Workspaceから退出できません。"
            "先にOwnerを移譲してください。"
        )

    membership = (
        _get_locked_membership(
            workspace=locked_workspace,
            user=user,
        )
    )

    if not membership:
        raise ValidationError(
            "Workspaceメンバーではありません。"
        )

    membership.is_active = False
    membership.left_at = timezone.now()

    membership.save(
        update_fields=(
            "is_active",
            "left_at",
            "updated_at",
        )
    )

    return membership


@transaction.atomic
def transfer_workspace_ownership(
    *,
    workspace,
    current_owner,
    target_membership_id,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    if (
        locked_workspace.owner_id
        != current_owner.id
    ):
        raise PermissionDenied(
            "Owner移譲は現在のOwnerのみ"
            "実行できます。"
        )

    current_owner_membership = (
        WorkspaceMember.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=locked_workspace,
            user=current_owner,
            is_active=True,
        )
        .first()
    )

    if not current_owner_membership:
        raise ValidationError(
            "Owner Membershipが"
            "見つかりません。"
        )

    target_membership = (
        WorkspaceMember.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=target_membership_id,
            workspace=locked_workspace,
            is_active=True,
        )
        .first()
    )

    if not target_membership:
        raise ValidationError(
            "移譲先メンバーが"
            "存在しません。"
        )

    if (
        target_membership.user_id
        == current_owner.id
    ):
        raise ValidationError(
            "自分自身には移譲できません。"
        )

    if (
        target_membership.role
        == WorkspaceMember.Role.GUEST
    ):
        raise ValidationError(
            "GuestへOwnerを"
            "移譲できません。"
            "先にMemberへ変更してください。"
        )

    target_membership.role = (
        WorkspaceMember.Role.OWNER
    )

    target_membership.save(
        update_fields=(
            "role",
            "updated_at",
        )
    )

    current_owner_membership.role = (
        WorkspaceMember.Role.ADMIN
    )

    current_owner_membership.save(
        update_fields=(
            "role",
            "updated_at",
        )
    )

    locked_workspace.owner = (
        target_membership.user
    )

    locked_workspace.save(
        update_fields=(
            "owner",
            "updated_at",
        )
    )

    return locked_workspace


def _validate_invitation_permission(
    *,
    workspace,
    actor,
    role,
):
    actor_role = _require_manager(
        workspace=workspace,
        actor=actor,
    )

    if (
        actor_role
        == WorkspaceMember.Role.ADMIN
        and role
        == WorkspaceInvitation.Role.ADMIN
    ):
        raise PermissionDenied(
            "Admin招待を作成できるのは"
            "Ownerのみです。"
        )


@transaction.atomic
def create_workspace_invitation(
    *,
    workspace,
    created_by,
    role=WorkspaceInvitation.Role.MEMBER,
    expires_in_days=7,
    max_uses=1,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    _validate_invitation_permission(
        workspace=locked_workspace,
        actor=created_by,
        role=role,
    )

    if role not in (
        WorkspaceInvitation.Role.ADMIN,
        WorkspaceInvitation.Role.MEMBER,
        WorkspaceInvitation.Role.GUEST,
    ):
        raise ValidationError(
            "招待Roleが不正です。"
        )

    if not (
        1
        <= expires_in_days
        <= 30
    ):
        raise ValidationError(
            "招待の有効期限は"
            "1〜30日で指定してください。"
        )

    if not (
        1
        <= max_uses
        <= 100
    ):
        raise ValidationError(
            "招待の使用回数は"
            "1〜100回で指定してください。"
        )

    token = secrets.token_urlsafe(
        32
    )

    invitation = (
        WorkspaceInvitation.objects.create(
            workspace=locked_workspace,
            token_hash=(
                hash_invitation_token(
                    token
                )
            ),
            role=role,
            created_by=created_by,
            expires_at=(
                timezone.now()
                + timedelta(
                    days=expires_in_days
                )
            ),
            max_uses=max_uses,
            use_count=0,
            is_active=True,
        )
    )

    return (
        invitation,
        token,
    )


@transaction.atomic
def revoke_workspace_invitation(
    *,
    workspace,
    actor,
    invitation_id,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    _require_manager(
        workspace=locked_workspace,
        actor=actor,
    )

    invitation = (
        WorkspaceInvitation.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=invitation_id,
            workspace=locked_workspace,
        )
        .first()
    )

    if not invitation:
        raise ValidationError(
            "招待が存在しません。"
        )

    if (
        invitation.role
        == WorkspaceInvitation.Role.ADMIN
        and locked_workspace.owner_id
        != actor.id
    ):
        raise PermissionDenied(
            "Admin招待を無効化できるのは"
            "Ownerのみです。"
        )

    if not invitation.is_active:
        return invitation

    invitation.is_active = False
    invitation.revoked_at = (
        timezone.now()
    )
    invitation.revoked_by = actor

    invitation.save(
        update_fields=(
            "is_active",
            "revoked_at",
            "revoked_by",
            "updated_at",
        )
    )

    return invitation


@transaction.atomic
def reissue_workspace_invitation(
    *,
    workspace,
    actor,
    invitation_id,
    expires_in_days=7,
    max_uses=None,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    invitation = (
        WorkspaceInvitation.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=invitation_id,
            workspace=locked_workspace,
        )
        .first()
    )

    if not invitation:
        raise ValidationError(
            "招待が存在しません。"
        )

    _validate_invitation_permission(
        workspace=locked_workspace,
        actor=actor,
        role=invitation.role,
    )

    invitation.is_active = False
    invitation.revoked_at = (
        timezone.now()
    )
    invitation.revoked_by = actor

    invitation.save(
        update_fields=(
            "is_active",
            "revoked_at",
            "revoked_by",
            "updated_at",
        )
    )

    if max_uses is None:
        max_uses = (
            invitation.max_uses
        )

    return create_workspace_invitation(
        workspace=locked_workspace,
        created_by=actor,
        role=invitation.role,
        expires_in_days=(
            expires_in_days
        ),
        max_uses=max_uses,
    )


@transaction.atomic
def accept_workspace_invitation(
    *,
    user,
    token,
):
    normalized_token = (
        token.strip()
    )

    if not normalized_token:
        raise ValidationError(
            "招待コードを入力してください。"
        )

    token_hash = (
        hash_invitation_token(
            normalized_token
        )
    )

    invitation = (
        WorkspaceInvitation.objects
        .select_for_update(
            of=("self",)
        )
        .select_related(
            "workspace",
        )
        .filter(
            token_hash=token_hash,
        )
        .first()
    )

    if not invitation:
        raise ValidationError(
            "招待コードが無効です。"
        )

    now = timezone.now()

    if not invitation.is_active:
        raise ValidationError(
            "この招待は無効です。"
        )

    if (
        invitation.expires_at
        <= now
    ):
        invitation.is_active = False

        invitation.save(
            update_fields=(
                "is_active",
                "updated_at",
            )
        )

        raise ValidationError(
            "この招待の有効期限は"
            "切れています。"
        )

    if (
        invitation.use_count
        >= invitation.max_uses
    ):
        invitation.is_active = False

        invitation.save(
            update_fields=(
                "is_active",
                "updated_at",
            )
        )

        raise ValidationError(
            "この招待は使用上限に"
            "達しています。"
        )

    workspace = (
        _get_locked_workspace(
            invitation.workspace
        )
    )

    membership = (
        WorkspaceMember.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=workspace,
            user=user,
        )
        .first()
    )

    if (
        membership
        and membership.is_active
    ):
        raise ValidationError(
            "すでにWorkspaceへ"
            "参加しています。"
        )

    if membership:
        membership.role = (
            invitation.role
        )

        membership.is_active = True
        membership.left_at = None

        membership.save(
            update_fields=(
                "role",
                "is_active",
                "left_at",
                "updated_at",
            )
        )

    else:
        membership = (
            WorkspaceMember.objects
            .create(
                workspace=workspace,
                user=user,
                role=invitation.role,
                is_active=True,
            )
        )

    invitation.use_count += 1

    if (
        invitation.use_count
        >= invitation.max_uses
    ):
        invitation.is_active = False

    invitation.save(
        update_fields=(
            "use_count",
            "is_active",
            "updated_at",
        )
    )

    record_workspace_member_joined(
        workspace=workspace,
        actor=user,
        member_user=user,
        role=membership.role,
    )

    notify_workspace_member_joined(
        workspace=workspace,
        actor=user,
        member_user=user,
        role=membership.role,
    )

    return membership