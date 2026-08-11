from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from activity.models import ActivityEvent
from scheduling.models import (
    CalendarEvent,
    CalendarEventParticipant,
)
from tasks.models import (
    Task,
    TaskAssignee,
    TaskStatus,
)
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from integrations.models import (
    WorkspaceGitHubRepository,
)
from notifications.models import (
    Notification,
)


def get_accessible_workspaces(
    *,
    user,
):
    member_workspace_ids = (
        WorkspaceMember.objects
        .filter(
            user=user,
            is_active=True,
        )
        .values_list(
            "workspace_id",
            flat=True,
        )
    )

    return (
        Workspace.objects
        .filter(
            Q(owner=user)
            | Q(
                id__in=(
                    member_workspace_ids
                )
            )
        )
        .distinct()
    )


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


def get_user_task_ids(
    *,
    user,
):
    assigned_task_ids = (
        TaskAssignee.objects
        .filter(
            user=user,
        )
        .values_list(
            "task_id",
            flat=True,
        )
    )

    return (
        Task.objects
        .filter(
            Q(created_by=user)
            | Q(
                id__in=(
                    assigned_task_ids
                )
            ),
            deleted_at__isnull=True,
        )
        .values_list(
            "id",
            flat=True,
        )
        .distinct()
    )


def get_open_user_tasks(
    *,
    user,
):
    task_ids = get_user_task_ids(
        user=user,
    )

    return (
        Task.objects
        .filter(
            id__in=task_ids,
            deleted_at__isnull=True,
        )
        .exclude(
            status=TaskStatus.DONE,
        )
        .select_related(
            "workspace",
            "created_by",
        )
        .order_by(
            "due_at",
            "created_at",
        )
    )


def get_today_tasks(
    *,
    user,
):
    today = timezone.localdate()

    return (
        get_open_user_tasks(
            user=user,
        )
        .filter(
            due_at__date=today,
        )
    )


def get_overdue_tasks(
    *,
    user,
):
    today = timezone.localdate()

    return (
        get_open_user_tasks(
            user=user,
        )
        .filter(
            due_at__date__lt=today,
        )
    )


def get_user_calendar_event_ids(
    *,
    user,
):
    participant_event_ids = (
        CalendarEventParticipant.objects
        .filter(
            user=user,
        )
        .values_list(
            "event_id",
            flat=True,
        )
    )

    return (
        CalendarEvent.objects
        .filter(
            Q(created_by=user)
            | Q(
                id__in=(
                    participant_event_ids
                )
            ),
            deleted_at__isnull=True,
        )
        .values_list(
            "id",
            flat=True,
        )
        .distinct()
    )


def get_today_calendar_events(
    *,
    user,
):
    today = timezone.localdate()

    start_of_day = (
        timezone.make_aware(
            timezone.datetime.combine(
                today,
                timezone.datetime.min.time(),
            )
        )
    )

    end_of_day = (
        start_of_day
        + timedelta(
            days=1
        )
    )

    event_ids = (
        get_user_calendar_event_ids(
            user=user,
        )
    )

    return (
        CalendarEvent.objects
        .filter(
            id__in=event_ids,
            deleted_at__isnull=True,
        )
        .filter(
            Q(
                is_all_day=True,
                start_date__lte=today,
                end_date__gte=today,
            )
            |
            Q(
                is_all_day=False,
                starts_at__lt=end_of_day,
                ends_at__gte=start_of_day,
            )
        )
        .select_related(
            "workspace",
            "created_by",
        )
        .order_by(
            "is_all_day",
            "starts_at",
            "start_date",
        )
    )


def get_next_calendar_event(
    *,
    user,
):
    now = timezone.now()

    today = timezone.localdate()

    event_ids = (
        get_user_calendar_event_ids(
            user=user,
        )
    )

    timed_event = (
        CalendarEvent.objects
        .filter(
            id__in=event_ids,
            deleted_at__isnull=True,
            is_all_day=False,
            starts_at__gte=now,
        )
        .select_related(
            "workspace",
        )
        .order_by(
            "starts_at",
        )
        .first()
    )

    if timed_event is not None:
        return timed_event

    return (
        CalendarEvent.objects
        .filter(
            id__in=event_ids,
            deleted_at__isnull=True,
            is_all_day=True,
            start_date__gte=today,
        )
        .select_related(
            "workspace",
        )
        .order_by(
            "start_date",
        )
        .first()
    )


def get_visible_workspace_activity(
    *,
    workspace,
    user,
):
    role = get_workspace_role(
        workspace=workspace,
        user=user,
    )

    queryset = (
        ActivityEvent.objects
        .filter(
            workspace=workspace,
        )
        .select_related(
            "workspace",
            "actor",
            "subject_user",
        )
    )

    if role in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
    ):
        return queryset

    if role == WorkspaceMember.Role.MEMBER:
        return queryset.filter(
            visibility__in=(
                ActivityEvent.Visibility.ALL_MEMBERS,
                ActivityEvent.Visibility.CONTRIBUTORS,
            )
        )

    if role == WorkspaceMember.Role.GUEST:
        return queryset.filter(
            visibility=(
                ActivityEvent.Visibility.ALL_MEMBERS
            )
        )

    return queryset.none()


def get_project_pulse(
    *,
    user,
    limit=12,
):
    workspaces = list(
        get_accessible_workspaces(
            user=user,
        )
    )

    events = []

    for workspace in workspaces:
        workspace_events = list(
            get_visible_workspace_activity(
                workspace=workspace,
                user=user,
            )[:limit]
        )

        events.extend(
            workspace_events
        )

    events.sort(
        key=lambda event: (
            event.occurred_at
        ),
        reverse=True,
    )

    return events[:limit]


def get_latest_workspace_activity(
    *,
    workspace,
    user,
):
    return (
        get_visible_workspace_activity(
            workspace=workspace,
            user=user,
        )
        .order_by(
            "-occurred_at",
        )
        .first()
    )


def get_workspace_open_task_count(
    *,
    workspace,
):
    return (
        Task.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=True,
        )
        .exclude(
            status=TaskStatus.DONE,
        )
        .count()
    )


def get_workspace_overdue_task_count(
    *,
    workspace,
):
    today = timezone.localdate()

    return (
        Task.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=True,
            due_at__date__lt=today,
        )
        .exclude(
            status=TaskStatus.DONE,
        )
        .count()
    )


def get_workspace_upcoming_event_count(
    *,
    workspace,
):
    now = timezone.now()

    until = (
        now
        + timedelta(
            days=7
        )
    )

    return (
        CalendarEvent.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=True,
            is_all_day=False,
            starts_at__gte=now,
            starts_at__lte=until,
        )
        .count()
    )


def get_workspace_recent_activity_count(
    *,
    workspace,
    user,
):
    since = (
        timezone.now()
        - timedelta(
            days=7
        )
    )

    return (
        get_visible_workspace_activity(
            workspace=workspace,
            user=user,
        )
        .filter(
            occurred_at__gte=since,
        )
        .count()
    )


def get_workspace_member_count(
    *,
    workspace,
):
    active_members = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            is_active=True,
        )
    )

    count = active_members.count()

    owner_exists = (
        active_members
        .filter(
            user_id=workspace.owner_id,
        )
        .exists()
    )

    if not owner_exists:
        count += 1

    return count


def get_workspace_github_summary(
    *,
    workspace,
):
    repositories = (
        WorkspaceGitHubRepository.objects
        .filter(
            workspace=workspace,
            unlinked_at__isnull=True,
        )
    )

    primary = (
        repositories
        .filter(
            is_primary=True,
        )
        .first()
    )

    return {
        "linked_repository_count": (
            repositories.count()
        ),
        "primary_repository": (
            primary
        ),
    }


def get_workspace_unread_notification_count(
    *,
    workspace,
    user,
):
    return (
        Notification.objects
        .filter(
            recipient=user,
            workspace=workspace,
            read_at__isnull=True,
        )
        .count()
    )


def get_unread_notification_count(
    *,
    user,
):
    return (
        Notification.objects
        .filter(
            recipient=user,
            read_at__isnull=True,
        )
        .count()
    )