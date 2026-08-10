from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import (
    IntegrityError,
    transaction,
)
from django.db.models import Max
from django.utils import timezone
from django.utils.text import slugify

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from activity.recorders import (
    record_channel_created,
    record_message_sent,
)

from notifications.recorders import (
    notify_message_reply,
)

from .models import (
    Channel,
    Message,
)


def _get_actor_role(
    *,
    workspace,
    actor,
):
    if workspace.owner_id == actor.id:
        return WorkspaceMember.Role.OWNER

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


def _require_workspace_member(
    *,
    workspace,
    user,
):
    if workspace.owner_id == user.id:
        return

    exists = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .exists()
    )

    if not exists:
        raise PermissionDenied(
            "Workspaceメンバーではありません。"
        )


def _require_channel_manager(
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
            "Channelを管理できるのは"
            "OwnerまたはAdminのみです。"
        )

    return role


def _normalize_channel_name(
    name,
):
    normalized = slugify(
        name.strip(),
        allow_unicode=True,
    )

    if not normalized:
        raise ValidationError(
            "Channel名を入力してください。"
        )

    if len(normalized) > 80:
        raise ValidationError(
            "Channel名は80文字以内で"
            "入力してください。"
        )

    return normalized


@transaction.atomic
def create_channel(
    *,
    workspace,
    actor,
    name,
    description="",
):
    locked_workspace = (
        Workspace.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace.id,
        )
    )

    _require_channel_manager(
        workspace=locked_workspace,
        actor=actor,
    )

    normalized_name = (
        _normalize_channel_name(
            name
        )
    )

    if (
        Channel.objects
        .filter(
            workspace=locked_workspace,
            name=normalized_name,
            is_archived=False,
        )
        .exists()
    ):
        raise ValidationError(
            "同じ名前のChannelが"
            "すでに存在します。"
        )

    current_max = (
        Channel.objects
        .filter(
            workspace=locked_workspace,
            is_archived=False,
        )
        .aggregate(
            max_position=Max(
                "position"
            )
        )["max_position"]
    )

    position = (
        0
        if current_max is None
        else current_max + 1
    )

    try:
        channel = Channel.objects.create(
            workspace=locked_workspace,
            name=normalized_name,
            description=(
                description.strip()
            ),
            channel_type=(
                Channel.ChannelType.TEXT
            ),
            position=position,
            created_by=actor,
        )

    except IntegrityError as error:
        raise ValidationError(
            "同じ名前のChannelが"
            "すでに存在します。"
        ) from error

    record_channel_created(
        workspace=locked_workspace,
        actor=actor,
        channel=channel,
    )

    return channel


def create_text_channel(
    *,
    workspace,
    created_by=None,
    actor=None,
    name,
    description="",
):
    channel_actor = (
        actor
        or created_by
    )

    if channel_actor is None:
        raise ValidationError(
            "Channel作成者が必要です。"
        )

    return create_channel(
        workspace=workspace,
        actor=channel_actor,
        name=name,
        description=description,
    )


@transaction.atomic
def update_channel(
    *,
    channel,
    actor,
    name=None,
    description=None,
):
    locked_channel = (
        Channel.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=channel.id,
        )
    )

    _require_channel_manager(
        workspace=(
            locked_channel.workspace
        ),
        actor=actor,
    )

    if locked_channel.is_archived:
        raise ValidationError(
            "Archive済みChannelは"
            "編集できません。"
        )

    update_fields = []

    if name is not None:
        normalized_name = (
            _normalize_channel_name(
                name
            )
        )

        conflict = (
            Channel.objects
            .filter(
                workspace=(
                    locked_channel.workspace
                ),
                name=normalized_name,
                is_archived=False,
            )
            .exclude(
                id=locked_channel.id,
            )
            .exists()
        )

        if conflict:
            raise ValidationError(
                "同じ名前のChannelが"
                "すでに存在します。"
            )

        locked_channel.name = (
            normalized_name
        )

        update_fields.append(
            "name"
        )

    if description is not None:
        locked_channel.description = (
            description.strip()
        )

        update_fields.append(
            "description"
        )

    if not update_fields:
        return locked_channel

    update_fields.append(
        "updated_at"
    )

    try:
        locked_channel.save(
            update_fields=tuple(
                update_fields
            )
        )

    except IntegrityError as error:
        raise ValidationError(
            "同じ名前のChannelが"
            "すでに存在します。"
        ) from error

    return locked_channel


@transaction.atomic
def archive_channel(
    *,
    channel,
    actor,
):
    locked_channel = (
        Channel.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=channel.id,
        )
    )

    _require_channel_manager(
        workspace=(
            locked_channel.workspace
        ),
        actor=actor,
    )

    if locked_channel.is_archived:
        return locked_channel

    locked_channel.is_archived = True

    locked_channel.archived_at = (
        timezone.now()
    )

    locked_channel.archived_by = actor

    locked_channel.save(
        update_fields=(
            "is_archived",
            "archived_at",
            "archived_by",
            "updated_at",
        )
    )

    return locked_channel


@transaction.atomic
def restore_channel(
    *,
    channel,
    actor,
):
    locked_channel = (
        Channel.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=channel.id,
        )
    )

    workspace = (
        locked_channel.workspace
    )

    _require_channel_manager(
        workspace=workspace,
        actor=actor,
    )

    if not locked_channel.is_archived:
        return locked_channel

    conflict = (
        Channel.objects
        .filter(
            workspace=workspace,
            name=locked_channel.name,
            is_archived=False,
        )
        .exclude(
            id=locked_channel.id,
        )
        .exists()
    )

    if conflict:
        raise ValidationError(
            "同じ名前のActive Channelが"
            "存在するためRestoreできません。"
        )

    current_max = (
        Channel.objects
        .filter(
            workspace=workspace,
            is_archived=False,
        )
        .aggregate(
            max_position=Max(
                "position"
            )
        )["max_position"]
    )

    locked_channel.position = (
        0
        if current_max is None
        else current_max + 1
    )

    locked_channel.is_archived = False
    locked_channel.archived_at = None
    locked_channel.archived_by = None

    try:
        locked_channel.save(
            update_fields=(
                "position",
                "is_archived",
                "archived_at",
                "archived_by",
                "updated_at",
            )
        )

    except IntegrityError as error:
        raise ValidationError(
            "ChannelをRestoreできません。"
        ) from error

    return locked_channel


@transaction.atomic
def reorder_channels(
    *,
    workspace,
    actor,
    channel_ids,
):
    locked_workspace = (
        Workspace.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace.id,
        )
    )

    _require_channel_manager(
        workspace=locked_workspace,
        actor=actor,
    )

    channels = list(
        Channel.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=locked_workspace,
            is_archived=False,
        )
        .order_by(
            "position",
            "created_at",
        )
    )

    existing_ids = {
        channel.id
        for channel in channels
    }

    requested_ids = list(
        channel_ids
    )

    if len(requested_ids) != len(
        set(requested_ids)
    ):
        raise ValidationError(
            "Channel IDが重複しています。"
        )

    if set(requested_ids) != existing_ids:
        raise ValidationError(
            "並び替えにはActive Channelを"
            "すべて指定してください。"
        )

    channel_map = {
        channel.id: channel
        for channel in channels
    }

    now = timezone.now()

    ordered_channels = []

    for position, channel_id in enumerate(
        requested_ids
    ):
        channel = (
            channel_map[channel_id]
        )

        channel.position = position
        channel.updated_at = now

        ordered_channels.append(
            channel
        )

    Channel.objects.bulk_update(
        ordered_channels,
        fields=(
            "position",
            "updated_at",
        ),
    )

    return ordered_channels


@transaction.atomic
def create_message(
    *,
    channel,
    author,
    content,
    reply_to=None,
):
    locked_channel = (
        Channel.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=channel.id,
        )
    )

    _require_workspace_member(
        workspace=(
            locked_channel.workspace
        ),
        user=author,
    )

    if locked_channel.is_archived:
        raise ValidationError(
            "Archive済みChannelには"
            "投稿できません。"
        )

    if (
        locked_channel.channel_type
        != Channel.ChannelType.TEXT
    ):
        raise ValidationError(
            "Text Channelにのみ"
            "Messageを投稿できます。"
        )

    normalized_content = (
        content.strip()
    )

    if not normalized_content:
        raise ValidationError(
            "Messageを入力してください。"
        )

    if len(normalized_content) > 4000:
        raise ValidationError(
            "Messageは4000文字以内で"
            "入力してください。"
        )

    if reply_to:
        if (
            reply_to.channel_id
            != locked_channel.id
        ):
            raise ValidationError(
                "別ChannelのMessageには"
                "返信できません。"
            )

        if reply_to.deleted_at:
            raise ValidationError(
                "削除済みMessageには"
                "返信できません。"
            )

    message = Message.objects.create(
        channel=locked_channel,
        author=author,
        content=normalized_content,
        reply_to=reply_to,
    )

    record_message_sent(
        workspace=locked_channel.workspace,
        actor=author,
        message=message,
        channel=locked_channel,
    )

    if reply_to is not None:
        notify_message_reply(
            workspace=locked_channel.workspace,
            actor=author,
            message=message,
            reply_to=reply_to,
            channel=locked_channel,
        )

    return message


@transaction.atomic
def update_message(
    *,
    message,
    actor,
    content,
):
    locked_message = (
        Message.objects
        .select_related(
            "channel__workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=message.id,
        )
    )

    if locked_message.deleted_at:
        raise ValidationError(
            "削除済みMessageは"
            "編集できません。"
        )

    if (
        locked_message.author_id
        != actor.id
    ):
        raise PermissionDenied(
            "自分のMessageのみ"
            "編集できます。"
        )

    if (
        locked_message.channel
        .is_archived
    ):
        raise ValidationError(
            "Archive済みChannelの"
            "Messageは編集できません。"
        )

    normalized_content = (
        content.strip()
    )

    if not normalized_content:
        raise ValidationError(
            "Messageを入力してください。"
        )

    if len(normalized_content) > 4000:
        raise ValidationError(
            "Messageは4000文字以内で"
            "入力してください。"
        )

    locked_message.content = (
        normalized_content
    )

    locked_message.is_edited = True

    locked_message.save(
        update_fields=(
            "content",
            "is_edited",
            "updated_at",
        )
    )

    return locked_message


@transaction.atomic
def delete_message(
    *,
    message,
    actor,
):
    locked_message = (
        Message.objects
        .select_related(
            "channel__workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=message.id,
        )
    )

    if locked_message.deleted_at:
        return locked_message

    workspace = (
        locked_message
        .channel
        .workspace
    )

    actor_is_author = (
        locked_message.author_id
        == actor.id
    )

    actor_role = _get_actor_role(
        workspace=workspace,
        actor=actor,
    )

    actor_is_manager = (
        actor_role
        in (
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        )
    )

    if (
        not actor_is_author
        and not actor_is_manager
    ):
        raise PermissionDenied(
            "Messageを削除する権限が"
            "ありません。"
        )

    locked_message.content = ""

    locked_message.deleted_at = (
        timezone.now()
    )

    locked_message.deleted_by = actor

    locked_message.save(
        update_fields=(
            "content",
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return locked_message