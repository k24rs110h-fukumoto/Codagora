from django.db.models import (
    Count,
    Prefetch,
    Q,
)
from django.utils import timezone

from .models import (
    Task,
    TaskAssignee,
    TaskComment,
)


def get_workspace_tasks(
    *,
    workspace,
):
    assignees = (
        TaskAssignee.objects
        .select_related(
            "user",
        )
        .order_by(
            "assigned_at",
        )
    )

    return (
        Task.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=True,
        )
        .select_related(
            "workspace",
            "created_by",
        )
        .prefetch_related(
            Prefetch(
                "task_assignees",
                queryset=assignees,
                to_attr=(
                    "prefetched_assignees"
                ),
            )
        )
        .annotate(
            active_comment_count=Count(
                "comments",
                filter=Q(
                    comments__deleted_at__isnull=True,
                ),
            )
        )
    )


def filter_workspace_tasks(
    *,
    queryset,
    status=None,
    priority=None,
    assignee_id=None,
    search=None,
    overdue=None,
):
    if status:
        queryset = queryset.filter(
            status=status,
        )

    if priority:
        queryset = queryset.filter(
            priority=priority,
        )

    if assignee_id:
        queryset = queryset.filter(
            task_assignees__user_id=(
                assignee_id
            ),
        )

    if search:
        queryset = queryset.filter(
            Q(
                title__icontains=search
            )
            | Q(
                description__icontains=search
            )
        )

    if overdue is True:
        queryset = queryset.filter(
            due_at__lt=timezone.now(),
        ).exclude(
            status__in=(
                "done",
                "canceled",
            )
        )

    if overdue is False:
        queryset = queryset.exclude(
            due_at__lt=timezone.now(),
        )

    return queryset.distinct()


def get_task_comments(
    *,
    task,
):
    return (
        TaskComment.objects
        .filter(
            task=task,
            deleted_at__isnull=True,
        )
        .select_related(
            "author",
        )
        .order_by(
            "created_at",
        )
    )