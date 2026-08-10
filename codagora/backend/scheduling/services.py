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
    record_calendar_created,
    record_calendar_updated,
)

from notifications.recorders import (
    notify_calendar_invited,
    notify_calendar_updated,
)

from .models import (
    CalendarEvent,
    CalendarEventParticipant,
    ParticipantResponse,
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


def require_contributor(
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
            "予定を作成するには"
            "Member以上の権限が必要です。"
        )

    return role


def can_manage_event(
    *,
    event,
    user,
):
    role = get_workspace_role(
        workspace=event.workspace,
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
        or event.created_by_id
        == user.id
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


def validate_participants(
    *,
    workspace,
    participant_ids,
):
    requested = set(
        participant_ids
    )

    if not requested:
        return []

    memberships = list(
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user_id__in=requested,
            is_active=True,
        )
        .select_related(
            "user",
        )
    )

    found = {
        membership.user_id
        for membership
        in memberships
    }

    if found != requested:
        raise ValidationError(
            "参加者にはActiveな"
            "Workspaceメンバーのみ"
            "指定できます。"
        )

    return [
        membership.user
        for membership
        in memberships
    ]


def sync_participants(
    *,
    event,
    users,
    actor,
):
    users_by_id = {
        user.id: user
        for user in users
    }

    if event.created_by:
        users_by_id[
            event.created_by_id
        ] = event.created_by

    existing = {
        participant.user_id:
        participant
        for participant
        in (
            CalendarEventParticipant
            .objects
            .select_for_update(
                of=("self",)
            )
            .filter(
                event=event,
            )
        )
    }

    wanted_ids = set(
        users_by_id.keys()
    )

    for user_id, participant in (
        existing.items()
    ):
        if (
            user_id not in wanted_ids
            and user_id
            != event.created_by_id
        ):
            participant.delete()

    to_create = []

    for user_id, user in (
        users_by_id.items()
    ):
        if user_id in existing:
            continue

        response = (
            ParticipantResponse.ACCEPTED
            if user_id
            == event.created_by_id
            else ParticipantResponse.PENDING
        )

        to_create.append(
            CalendarEventParticipant(
                event=event,
                user=user,
                response=response,
                added_by=actor,
            )
        )

    CalendarEventParticipant.objects.bulk_create(
        to_create
    )


@transaction.atomic
def create_calendar_event(
    *,
    workspace,
    actor,
    data,
):
    locked_workspace = (
        get_locked_workspace(
            workspace
        )
    )

    require_contributor(
        workspace=locked_workspace,
        user=actor,
    )

    participant_ids = (
        data.pop(
            "participant_ids",
            [],
        )
    )

    participants = (
        validate_participants(
            workspace=locked_workspace,
            participant_ids=(
                participant_ids
            ),
        )
    )

    event = (
        CalendarEvent.objects.create(
            workspace=locked_workspace,
            created_by=actor,
            **data,
        )
    )

    sync_participants(
        event=event,
        users=participants,
        actor=actor,
    )

    record_calendar_created(
        workspace=locked_workspace,
        actor=actor,
        event=event,
    )

    notify_calendar_invited(
        workspace=locked_workspace,
        actor=actor,
        event=event,
        recipients=participants,
    )

    return event


@transaction.atomic
def update_calendar_event(
    *,
    event,
    actor,
    data,
):
    locked_event = (
        CalendarEvent.objects
        .select_related(
            "workspace",
            "created_by",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=event.id,
            deleted_at__isnull=True,
        )
    )

    if not can_manage_event(
        event=locked_event,
        user=actor,
    ):
        raise PermissionDenied(
            "この予定を編集する"
            "権限がありません。"
        )

    existing_participant_ids = set(
        CalendarEventParticipant.objects
        .filter(
            event=locked_event,
        )
        .values_list(
            "user_id",
            flat=True,
        )
    )

    participant_ids = (
        data.pop(
            "participant_ids",
            [],
        )
    )

    participants = (
        validate_participants(
            workspace=(
                locked_event.workspace
            ),
            participant_ids=(
                participant_ids
            ),
        )
    )

    editable_fields = (
        "title",
        "description",
        "location_name",
        "timezone",
        "is_all_day",
        "starts_at",
        "ends_at",
        "start_date",
        "end_date",
        "recurrence_frequency",
        "recurrence_interval",
        "recurrence_weekdays",
        "recurrence_until",
    )

    for field in editable_fields:
        setattr(
            locked_event,
            field,
            data[field],
        )

    locked_event.save(
        update_fields=(
            *editable_fields,
            "updated_at",
        )
    )

    sync_participants(
        event=locked_event,
        users=participants,
        actor=actor,
    )

    record_calendar_updated(
        workspace=locked_event.workspace,
        actor=actor,
        event=locked_event,
    )

    current_participants = list(
        CalendarEventParticipant.objects
        .filter(
            event=locked_event,
        )
        .select_related(
            "user",
        )
    )

    newly_invited_users = [
        participant.user
        for participant in current_participants
        if participant.user_id
        not in existing_participant_ids
    ]

    existing_users = [
        participant.user
        for participant in current_participants
        if participant.user_id
        in existing_participant_ids
    ]

    if newly_invited_users:
        notify_calendar_invited(
            workspace=locked_event.workspace,
            actor=actor,
            event=locked_event,
            recipients=newly_invited_users,
        )

    if existing_users:
        notify_calendar_updated(
            workspace=locked_event.workspace,
            actor=actor,
            event=locked_event,
            recipients=existing_users,
        )

    return locked_event


@transaction.atomic
def delete_calendar_event(
    *,
    event,
    actor,
):
    locked_event = (
        CalendarEvent.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=event.id,
        )
    )

    if locked_event.deleted_at:
        return locked_event

    if not can_manage_event(
        event=locked_event,
        user=actor,
    ):
        raise PermissionDenied(
            "この予定を削除する"
            "権限がありません。"
        )

    locked_event.deleted_at = (
        timezone.now()
    )

    locked_event.deleted_by = actor

    locked_event.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return locked_event


@transaction.atomic
def respond_to_calendar_event(
    *,
    event,
    user,
    response,
):
    participant = (
        CalendarEventParticipant
        .objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            event=event,
            user=user,
        )
        .first()
    )

    if not participant:
        raise ValidationError(
            "この予定の参加者では"
            "ありません。"
        )

    participant.response = response

    participant.save(
        update_fields=(
            "response",
            "updated_at",
        )
    )

    return participant