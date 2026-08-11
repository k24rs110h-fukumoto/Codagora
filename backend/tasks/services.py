from django.contrib.auth import (
    get_user_model,
)
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from activity.recorders import (
    record_task_completed,
    record_task_created,
    record_task_updated,
)

from notifications.recorders import (
    notify_task_assigned,
    notify_task_completed,
    notify_task_updated,
)

from .models import (
    Task,
    TaskAssignee,
    TaskComment,
    TaskStatus,
)


User = get_user_model()


def _get_workspace_role(
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


def _require_workspace_contributor(
    *,
    workspace,
    user,
):
    role = _get_workspace_role(
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


def _is_workspace_manager(
    *,
    workspace,
    user,
):
    role = _get_workspace_role(
        workspace=workspace,
        user=user,
    )

    return role in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
    )


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


def _validate_assignees(
    *,
    workspace,
    assignee_ids,
):
    requested_ids = set(
        assignee_ids
    )

    if not requested_ids:
        return []

    memberships = list(
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user_id__in=(
                requested_ids
            ),
            is_active=True,
            role__in=(
                WorkspaceMember.Role.OWNER,
                WorkspaceMember.Role.ADMIN,
                WorkspaceMember.Role.MEMBER,
            ),
        )
        .select_related(
            "user",
        )
    )

    found_ids = {
        membership.user_id
        for membership
        in memberships
    }

    if found_ids != requested_ids:
        raise ValidationError(
            "担当者にはActiveな"
            "Workspace Member以上のみ"
            "指定できます。"
        )

    return [
        membership.user
        for membership
        in memberships
    ]


def _next_position(
    *,
    workspace,
    status,
    exclude_task_id=None,
):
    queryset = (
        Task.objects
        .filter(
            workspace=workspace,
            status=status,
            deleted_at__isnull=True,
        )
    )

    if exclude_task_id:
        queryset = queryset.exclude(
            id=exclude_task_id,
        )

    max_position = queryset.aggregate(
        value=Max("position")
    )["value"]

    if max_position is None:
        return 0

    return max_position + 1


def _replace_assignees(
    *,
    task,
    users,
    actor,
):
    TaskAssignee.objects.filter(
        task=task,
    ).delete()

    TaskAssignee.objects.bulk_create(
        [
            TaskAssignee(
                task=task,
                user=user,
                assigned_by=actor,
            )
            for user in users
        ]
    )


def _get_task_notification_recipients(
    *,
    task,
):
    users = []
    seen_ids = set()

    if task.created_by_id:
        users.append(task.created_by)
        seen_ids.add(task.created_by_id)

    assignees = (
        TaskAssignee.objects
        .filter(
            task=task,
        )
        .select_related(
            "user",
        )
    )

    for assignee in assignees:
        if assignee.user_id in seen_ids:
            continue

        seen_ids.add(assignee.user_id)
        users.append(assignee.user)

    return users


@transaction.atomic
def create_task(
    *,
    workspace,
    actor,
    title,
    description="",
    status=TaskStatus.TODO,
    priority="medium",
    assignee_ids=None,
    due_at=None,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    _require_workspace_contributor(
        workspace=locked_workspace,
        user=actor,
    )

    normalized_title = (
        title.strip()
    )

    if not normalized_title:
        raise ValidationError(
            "Task名を入力してください。"
        )

    if assignee_ids is None:
        assignee_ids = []

    assignees = _validate_assignees(
        workspace=locked_workspace,
        assignee_ids=assignee_ids,
    )

    task = Task.objects.create(
        workspace=locked_workspace,
        title=normalized_title,
        description=(
            description.strip()
        ),
        status=status,
        priority=priority,
        due_at=due_at,
        created_by=actor,
        position=_next_position(
            workspace=locked_workspace,
            status=status,
        ),
        completed_at=(
            timezone.now()
            if status
            == TaskStatus.DONE
            else None
        ),
    )

    _replace_assignees(
        task=task,
        users=assignees,
        actor=actor,
    )

    record_task_created(
        workspace=locked_workspace,
        actor=actor,
        task=task,
    )

    notify_task_assigned(
        workspace=locked_workspace,
        actor=actor,
        task=task,
        recipients=assignees,
    )

    return task


@transaction.atomic
def update_task(
    *,
    task,
    actor,
    changes,
):
    workspace = (
        _get_locked_workspace(
            task.workspace
        )
    )

    locked_task = (
        Task.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=task.id,
            workspace=workspace,
            deleted_at__isnull=True,
        )
    )

    role = _require_workspace_contributor(
        workspace=workspace,
        user=actor,
    )

    previous_status = locked_task.status

    previous_assignee_ids = set(
        TaskAssignee.objects
        .filter(
            task=locked_task,
        )
        .values_list(
            "user_id",
            flat=True,
        )
    )

    is_manager = role in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
    )

    is_creator = (
        locked_task.created_by_id
        == actor.id
    )

    is_assignee = (
        TaskAssignee.objects
        .filter(
            task=locked_task,
            user=actor,
        )
        .exists()
    )

    if (
        not is_manager
        and not is_creator
        and not is_assignee
    ):
        raise PermissionDenied(
            "このTaskを編集する権限が"
            "ありません。"
        )

    if (
        is_assignee
        and not is_manager
        and not is_creator
    ):
        invalid_fields = (
            set(changes.keys())
            - {"status"}
        )

        if invalid_fields:
            raise PermissionDenied(
                "担当者はStatusのみ"
                "変更できます。"
            )

    update_fields = []

    if "title" in changes:
        normalized_title = (
            changes["title"].strip()
        )

        if not normalized_title:
            raise ValidationError(
                "Task名を入力してください。"
            )

        locked_task.title = (
            normalized_title
        )

        update_fields.append(
            "title"
        )

    if "description" in changes:
        locked_task.description = (
            changes[
                "description"
            ].strip()
        )

        update_fields.append(
            "description"
        )

    if "priority" in changes:
        locked_task.priority = (
            changes["priority"]
        )

        update_fields.append(
            "priority"
        )

    if "due_at" in changes:
        locked_task.due_at = (
            changes["due_at"]
        )

        update_fields.append(
            "due_at"
        )

    if "status" in changes:
        new_status = (
            changes["status"]
        )

        if (
            new_status
            != locked_task.status
        ):
            locked_task.status = (
                new_status
            )

            locked_task.position = (
                _next_position(
                    workspace=workspace,
                    status=new_status,
                    exclude_task_id=(
                        locked_task.id
                    ),
                )
            )

            update_fields.extend(
                (
                    "status",
                    "position",
                )
            )

            if (
                new_status
                == TaskStatus.DONE
            ):
                locked_task.completed_at = (
                    timezone.now()
                )

            else:
                locked_task.completed_at = (
                    None
                )

            update_fields.append(
                "completed_at"
            )

    if update_fields:
        update_fields.append(
            "updated_at"
        )

        locked_task.save(
            update_fields=tuple(
                set(update_fields)
            )
        )

    if "assignee_ids" in changes:
        if (
            not is_manager
            and not is_creator
        ):
            raise PermissionDenied(
                "担当者を変更する権限が"
                "ありません。"
            )

        assignees = (
            _validate_assignees(
                workspace=workspace,
                assignee_ids=(
                    changes[
                        "assignee_ids"
                    ]
                ),
            )
        )

        _replace_assignees(
            task=locked_task,
            users=assignees,
            actor=actor,
        )

        newly_assigned = [
            assignee
            for assignee in assignees
            if assignee.id
            not in previous_assignee_ids
        ]

        if newly_assigned:
            notify_task_assigned(
                workspace=workspace,
                actor=actor,
                task=locked_task,
                recipients=newly_assigned,
            )

    should_record_activity = (
        bool(update_fields)
        or "assignee_ids" in changes
    )

    if should_record_activity:
        notification_recipients = (
            _get_task_notification_recipients(
                task=locked_task,
            )
        )

        if (
            previous_status != TaskStatus.DONE
            and locked_task.status == TaskStatus.DONE
        ):
            record_task_completed(
                workspace=workspace,
                actor=actor,
                task=locked_task,
            )

            notify_task_completed(
                workspace=workspace,
                actor=actor,
                task=locked_task,
                recipients=(
                    notification_recipients
                ),
            )
        else:
            record_task_updated(
                workspace=workspace,
                actor=actor,
                task=locked_task,
            )

            if update_fields:
                notify_task_updated(
                    workspace=workspace,
                    actor=actor,
                    task=locked_task,
                    recipients=(
                        notification_recipients
                    ),
                )

    return locked_task


@transaction.atomic
def delete_task(
    *,
    task,
    actor,
):
    locked_task = (
        Task.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=task.id,
        )
    )

    if locked_task.deleted_at:
        return locked_task

    _require_workspace_contributor(
        workspace=locked_task.workspace,
        user=actor,
    )

    is_manager = (
        _is_workspace_manager(
            workspace=(
                locked_task.workspace
            ),
            user=actor,
        )
    )

    is_creator = (
        locked_task.created_by_id
        == actor.id
    )

    if (
        not is_manager
        and not is_creator
    ):
        raise PermissionDenied(
            "Taskを削除する権限が"
            "ありません。"
        )

    locked_task.deleted_at = (
        timezone.now()
    )

    locked_task.deleted_by = actor

    locked_task.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return locked_task


@transaction.atomic
def reorder_tasks(
    *,
    workspace,
    actor,
    status,
    task_ids,
):
    locked_workspace = (
        _get_locked_workspace(
            workspace
        )
    )

    _require_workspace_contributor(
        workspace=locked_workspace,
        user=actor,
    )

    tasks = list(
        Task.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            workspace=locked_workspace,
            status=status,
            deleted_at__isnull=True,
        )
        .order_by(
            "position",
            "created_at",
        )
    )

    existing_ids = {
        task.id
        for task in tasks
    }

    requested_ids = list(
        task_ids
    )

    if (
        set(requested_ids)
        != existing_ids
    ):
        raise ValidationError(
            "並び替え対象Statusの"
            "Taskをすべて指定してください。"
        )

    if len(requested_ids) != len(
        existing_ids
    ):
        raise ValidationError(
            "Task IDが重複しています。"
        )

    task_map = {
        task.id: task
        for task in tasks
    }

    now = timezone.now()

    ordered_tasks = []

    for position, task_id in enumerate(
        requested_ids
    ):
        task = task_map[
            task_id
        ]

        task.position = position
        task.updated_at = now

        ordered_tasks.append(
            task
        )

    Task.objects.bulk_update(
        ordered_tasks,
        fields=(
            "position",
            "updated_at",
        ),
    )

    return ordered_tasks


@transaction.atomic
def create_task_comment(
    *,
    task,
    actor,
    content,
):
    locked_task = (
        Task.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=task.id,
            deleted_at__isnull=True,
        )
    )

    _require_workspace_contributor(
        workspace=(
            locked_task.workspace
        ),
        user=actor,
    )

    normalized_content = (
        content.strip()
    )

    if not normalized_content:
        raise ValidationError(
            "コメントを入力してください。"
        )

    return (
        TaskComment.objects.create(
            task=locked_task,
            author=actor,
            content=normalized_content,
        )
    )


@transaction.atomic
def update_task_comment(
    *,
    comment,
    actor,
    content,
):
    locked_comment = (
        TaskComment.objects
        .select_related(
            "task__workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=comment.id,
            deleted_at__isnull=True,
        )
    )

    _require_workspace_contributor(
        workspace=(
            locked_comment
            .task
            .workspace
        ),
        user=actor,
    )

    if (
        locked_comment.author_id
        != actor.id
    ):
        raise PermissionDenied(
            "自分のコメントのみ"
            "編集できます。"
        )

    normalized_content = (
        content.strip()
    )

    if not normalized_content:
        raise ValidationError(
            "コメントを入力してください。"
        )

    locked_comment.content = (
        normalized_content
    )

    locked_comment.save(
        update_fields=(
            "content",
            "updated_at",
        )
    )

    return locked_comment


@transaction.atomic
def delete_task_comment(
    *,
    comment,
    actor,
):
    locked_comment = (
        TaskComment.objects
        .select_related(
            "task__workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=comment.id,
        )
    )

    if locked_comment.deleted_at:
        return locked_comment

    _require_workspace_contributor(
        workspace=(
            locked_comment
            .task
            .workspace
        ),
        user=actor,
    )

    is_author = (
        locked_comment.author_id
        == actor.id
    )

    is_manager = (
        _is_workspace_manager(
            workspace=(
                locked_comment
                .task
                .workspace
            ),
            user=actor,
        )
    )

    if (
        not is_author
        and not is_manager
    ):
        raise PermissionDenied(
            "コメントを削除する"
            "権限がありません。"
        )

    locked_comment.deleted_at = (
        timezone.now()
    )

    locked_comment.deleted_by = (
        actor
    )

    locked_comment.save(
        update_fields=(
            "deleted_at",
            "deleted_by",
            "updated_at",
        )
    )

    return locked_comment