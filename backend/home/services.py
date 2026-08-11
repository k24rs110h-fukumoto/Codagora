from datetime import timedelta

from django.utils import timezone

from activity.serializers import (
    ActivityEventSerializer,
)

from tasks.models import TaskStatus

from .selectors import (
    get_accessible_workspaces,
    get_latest_workspace_activity,
    get_next_calendar_event,
    get_open_user_tasks,
    get_overdue_tasks,
    get_project_pulse,
    get_today_calendar_events,
    get_today_tasks,
    get_unread_notification_count,
    get_workspace_github_summary,
    get_workspace_member_count,
    get_workspace_open_task_count,
    get_workspace_overdue_task_count,
    get_workspace_recent_activity_count,
    get_workspace_role,
    get_workspace_unread_notification_count,
    get_workspace_upcoming_event_count,
)


def serialize_task(
    task,
):
    return {
        "id": str(
            task.id
        ),
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "due_at": (
            task.due_at.isoformat()
            if task.due_at
            else None
        ),
        "workspace": {
            "id": str(
                task.workspace.id
            ),
            "slug": (
                task.workspace.slug
            ),
            "name": (
                task.workspace.name
            ),
        },
    }


def serialize_calendar_event(
    event,
):
    return {
        "id": str(
            event.id
        ),
        "title": event.title,
        "is_all_day": (
            event.is_all_day
        ),
        "starts_at": (
            event.starts_at.isoformat()
            if event.starts_at
            else None
        ),
        "ends_at": (
            event.ends_at.isoformat()
            if event.ends_at
            else None
        ),
        "start_date": (
            event.start_date.isoformat()
            if event.start_date
            else None
        ),
        "end_date": (
            event.end_date.isoformat()
            if event.end_date
            else None
        ),
        "workspace": {
            "id": str(
                event.workspace.id
            ),
            "slug": (
                event.workspace.slug
            ),
            "name": (
                event.workspace.name
            ),
        },
    }


def serialize_repository(
    repository,
):
    if repository is None:
        return None

    return {
        "id": str(
            repository.id
        ),
        "github_repository_id": (
            repository.github_repository_id
        ),
        "full_name": (
            repository.full_name
        ),
        "html_url": (
            repository.html_url
        ),
        "default_branch": (
            repository.default_branch
        ),
        "is_private": (
            repository.is_private
        ),
        "last_synced_at": (
            repository.last_synced_at.isoformat()
            if repository.last_synced_at
            else None
        ),
    }


def build_workspace_summary(
    *,
    workspace,
    user,
):
    latest_activity = (
        get_latest_workspace_activity(
            workspace=workspace,
            user=user,
        )
    )

    github = (
        get_workspace_github_summary(
            workspace=workspace,
        )
    )

    overdue_tasks = (
        get_workspace_overdue_task_count(
            workspace=workspace,
        )
    )

    open_tasks = (
        get_workspace_open_task_count(
            workspace=workspace,
        )
    )

    upcoming_events = (
        get_workspace_upcoming_event_count(
            workspace=workspace,
        )
    )

    activity_count = (
        get_workspace_recent_activity_count(
            workspace=workspace,
            user=user,
        )
    )

    unread_notifications = (
        get_workspace_unread_notification_count(
            workspace=workspace,
            user=user,
        )
    )

    last_activity_at = (
        latest_activity.occurred_at
        if latest_activity
        else None
    )

    recent_threshold = (
        timezone.now()
        - timedelta(
            hours=72
        )
    )

    if overdue_tasks > 0:
        state = "needs_attention"

    elif (
        last_activity_at
        and last_activity_at
        >= recent_threshold
    ):
        state = "active"

    elif (
        open_tasks > 0
        or upcoming_events > 0
    ):
        state = "active"

    else:
        state = "quiet"

    return {
        "id": str(
            workspace.id
        ),
        "slug": workspace.slug,
        "name": workspace.name,
        "role": get_workspace_role(
            workspace=workspace,
            user=user,
        ),
        "state": state,
        "last_activity_at": (
            last_activity_at.isoformat()
            if last_activity_at
            else None
        ),
        "metrics": {
            "open_tasks": open_tasks,
            "overdue_tasks": (
                overdue_tasks
            ),
            "upcoming_events": (
                upcoming_events
            ),
            "activity_7d": (
                activity_count
            ),
            "unread_notifications": (
                unread_notifications
            ),
            "members": (
                get_workspace_member_count(
                    workspace=workspace,
                )
            ),
            "linked_repositories": (
                github[
                    "linked_repository_count"
                ]
            ),
        },
        "primary_repository": (
            serialize_repository(
                github[
                    "primary_repository"
                ]
            )
        ),
    }


def build_active_workspaces(
    *,
    user,
):
    workspaces = list(
        get_accessible_workspaces(
            user=user,
        )
    )

    summaries = [
        build_workspace_summary(
            workspace=workspace,
            user=user,
        )
        for workspace in workspaces
    ]

    state_rank = {
        "needs_attention": 0,
        "active": 1,
        "quiet": 2,
    }

    summaries.sort(
        key=lambda item: (
            state_rank.get(
                item["state"],
                99,
            ),
            -(
                item[
                    "metrics"
                ][
                    "activity_7d"
                ]
            ),
            item["name"].lower(),
        )
    )

    return summaries


def build_continue_working(
    *,
    user,
    active_workspaces,
):
    if not active_workspaces:
        return None

    workspaces_by_id = {
        item["id"]: item
        for item
        in active_workspaces
    }

    pulse = get_project_pulse(
        user=user,
        limit=30,
    )

    for event in pulse:
        if event.workspace_id is None:
            continue

        workspace_id = str(
            event.workspace_id
        )

        if (
            workspace_id
            in workspaces_by_id
        ):
            workspace = (
                workspaces_by_id[
                    workspace_id
                ]
            )

            return {
                **workspace,
                "reason": (
                    "recent_activity"
                ),
            }

    for workspace in active_workspaces:
        if (
            workspace["state"]
            == "needs_attention"
        ):
            return {
                **workspace,
                "reason": (
                    "needs_attention"
                ),
            }

    return {
        **active_workspaces[0],
        "reason": "recent_workspace",
    }


def build_today(
    *,
    user,
):
    tasks = list(
        get_today_tasks(
            user=user,
        )
    )

    events = list(
        get_today_calendar_events(
            user=user,
        )
    )

    overdue = list(
        get_overdue_tasks(
            user=user,
        )
    )

    return {
        "date": (
            timezone.localdate()
            .isoformat()
        ),
        "tasks": [
            serialize_task(
                task
            )
            for task in tasks
        ],
        "events": [
            serialize_calendar_event(
                event
            )
            for event in events
        ],
        "summary": {
            "task_count": len(
                tasks
            ),
            "event_count": len(
                events
            ),
            "overdue_task_count": len(
                overdue
            ),
        },
    }


def build_next_move(
    *,
    user,
    continue_working,
):
    overdue_task = (
        get_overdue_tasks(
            user=user,
        )
        .order_by(
            "due_at",
            "created_at",
        )
        .first()
    )

    if overdue_task is not None:
        return {
            "type": "task",
            "reason": "overdue",
            "title": (
                "期限を過ぎたTaskがあります"
            ),
            "message": (
                f"「{overdue_task.title}」"
                "を確認するのがおすすめです。"
            ),
            "target": (
                serialize_task(
                    overdue_task
                )
            ),
        }

    today_task = (
        get_today_tasks(
            user=user,
        )
        .order_by(
            "due_at",
            "created_at",
        )
        .first()
    )

    if today_task is not None:
        return {
            "type": "task",
            "reason": "due_today",
            "title": (
                "今日のTaskがあります"
            ),
            "message": (
                f"「{today_task.title}」"
                "から進めるのがおすすめです。"
            ),
            "target": (
                serialize_task(
                    today_task
                )
            ),
        }

    next_event = (
        get_next_calendar_event(
            user=user,
        )
    )

    if next_event is not None:
        return {
            "type": "calendar",
            "reason": "upcoming_event",
            "title": (
                "次の予定を確認"
            ),
            "message": (
                f"次の予定は"
                f"「{next_event.title}」です。"
            ),
            "target": (
                serialize_calendar_event(
                    next_event
                )
            ),
        }

    open_task = (
        get_open_user_tasks(
            user=user,
        )
        .order_by(
            "updated_at",
        )
        .first()
    )

    if open_task is not None:
        return {
            "type": "task",
            "reason": "open_task",
            "title": (
                "次のTaskを進める"
            ),
            "message": (
                f"「{open_task.title}」"
                "を続けてみましょう。"
            ),
            "target": (
                serialize_task(
                    open_task
                )
            ),
        }

    if continue_working is not None:
        return {
            "type": "workspace",
            "reason": (
                "continue_workspace"
            ),
            "title": (
                "Workspaceを開く"
            ),
            "message": (
                f"「"
                f"{continue_working['name']}"
                f"」の続きを確認できます。"
            ),
            "target": {
                "id": (
                    continue_working[
                        "id"
                    ]
                ),
                "slug": (
                    continue_working[
                        "slug"
                    ]
                ),
                "name": (
                    continue_working[
                        "name"
                    ]
                ),
            },
        }

    return {
        "type": "none",
        "reason": "nothing_pending",
        "title": (
            "すべて順調です"
        ),
        "message": (
            "新しいWorkspaceやTaskを"
            "作成できます。"
        ),
        "target": None,
    }


def build_project_pulse(
    *,
    user,
):
    events = (
        get_project_pulse(
            user=user,
            limit=12,
        )
    )

    serializer = (
        ActivityEventSerializer(
            events,
            many=True,
        )
    )

    return serializer.data


def build_home_payload(
    *,
    user,
):
    active_workspaces = (
        build_active_workspaces(
            user=user,
        )
    )

    continue_working = (
        build_continue_working(
            user=user,
            active_workspaces=(
                active_workspaces
            ),
        )
    )

    return {
        "continue_working": (
            continue_working
        ),
        "today": build_today(
            user=user,
        ),
        "project_pulse": (
            build_project_pulse(
                user=user,
            )
        ),
        "next_move": (
            build_next_move(
                user=user,
                continue_working=(
                    continue_working
                ),
            )
        ),
        "active_workspaces": (
            active_workspaces
        ),
        "unread_notifications": (
            get_unread_notification_count(
                user=user,
            )
        ),
        "generated_at": (
            timezone.now()
            .isoformat()
        ),
    }