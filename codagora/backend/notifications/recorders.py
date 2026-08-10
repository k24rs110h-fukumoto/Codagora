from workspaces.models import WorkspaceMember

from .models import Notification
from .services import create_notification, create_notifications


def _workspace_manager_users(*, workspace):
    users = []
    seen_ids = set()

    if workspace.owner_id:
        users.append(workspace.owner)
        seen_ids.add(workspace.owner_id)

    memberships = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            is_active=True,
            role=WorkspaceMember.Role.ADMIN,
        )
        .select_related("user")
    )

    for membership in memberships:
        if membership.user_id in seen_ids:
            continue

        seen_ids.add(membership.user_id)
        users.append(membership.user)

    return users


def _workspace_contributor_users(*, workspace):
    users = []
    seen_ids = set()

    if workspace.owner_id:
        users.append(workspace.owner)
        seen_ids.add(workspace.owner_id)

    memberships = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            is_active=True,
            role__in=(
                WorkspaceMember.Role.ADMIN,
                WorkspaceMember.Role.MEMBER,
            ),
        )
        .select_related("user")
    )

    for membership in memberships:
        if membership.user_id in seen_ids:
            continue

        seen_ids.add(membership.user_id)
        users.append(membership.user)

    return users


def notify_workspace_member_joined(
    *,
    workspace,
    actor,
    member_user,
    role,
):
    return create_notifications(
        recipients=_workspace_manager_users(
            workspace=workspace,
        ),
        actor=actor,
        workspace=workspace,
        notification_type=(
            Notification.Type.WORKSPACE_MEMBER_JOINED
        ),
        category=Notification.Category.WORKSPACE,
        title="Workspace member joined",
        body=(
            f"{member_user.display_name or member_user.email} "
            "joined the workspace."
        ),
        object_type="workspace_member",
        object_id=member_user.id,
        metadata={
            "member_user_id": str(member_user.id),
            "role": role,
        },
    )


def notify_message_reply(
    *,
    workspace,
    actor,
    message,
    reply_to,
    channel,
):
    if reply_to is None or reply_to.author_id is None:
        return None

    return create_notification(
        recipient=reply_to.author,
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.MESSAGE_REPLY,
        category=Notification.Category.CHAT,
        title="New reply",
        body=f"A new reply was posted in #{channel.name}.",
        object_type="message",
        object_id=message.id,
        metadata={
            "channel_id": str(channel.id),
            "channel_name": channel.name,
            "reply_to_message_id": str(reply_to.id),
        },
    )


def notify_task_assigned(
    *,
    workspace,
    actor,
    task,
    recipients,
):
    return create_notifications(
        recipients=recipients,
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.TASK_ASSIGNED,
        category=Notification.Category.TASK,
        title="Task assigned",
        body=task.title,
        object_type="task",
        object_id=task.id,
        metadata={
            "task_title": task.title,
            "status": task.status,
            "priority": task.priority,
        },
    )


def notify_task_updated(
    *,
    workspace,
    actor,
    task,
    recipients,
):
    return create_notifications(
        recipients=recipients,
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.TASK_UPDATED,
        category=Notification.Category.TASK,
        title="Task updated",
        body=task.title,
        object_type="task",
        object_id=task.id,
        metadata={
            "task_title": task.title,
            "status": task.status,
            "priority": task.priority,
        },
    )


def notify_task_completed(
    *,
    workspace,
    actor,
    task,
    recipients,
):
    return create_notifications(
        recipients=recipients,
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.TASK_COMPLETED,
        category=Notification.Category.TASK,
        title="Task completed",
        body=task.title,
        object_type="task",
        object_id=task.id,
        metadata={
            "task_title": task.title,
        },
    )


def notify_calendar_invited(
    *,
    workspace,
    actor,
    event,
    recipients,
):
    return create_notifications(
        recipients=recipients,
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.CALENDAR_INVITED,
        category=Notification.Category.CALENDAR,
        title="Calendar invitation",
        body=event.title,
        object_type="calendar_event",
        object_id=event.id,
        metadata={
            "event_title": event.title,
            "is_all_day": event.is_all_day,
        },
    )


def notify_calendar_updated(
    *,
    workspace,
    actor,
    event,
    recipients,
):
    return create_notifications(
        recipients=recipients,
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.CALENDAR_UPDATED,
        category=Notification.Category.CALENDAR,
        title="Calendar event updated",
        body=event.title,
        object_type="calendar_event",
        object_id=event.id,
        metadata={
            "event_title": event.title,
            "is_all_day": event.is_all_day,
        },
    )


def notify_file_uploaded(
    *,
    workspace,
    actor,
    workspace_file,
):
    return create_notifications(
        recipients=_workspace_contributor_users(
            workspace=workspace,
        ),
        actor=actor,
        workspace=workspace,
        notification_type=Notification.Type.FILE_UPLOADED,
        category=Notification.Category.FILE,
        title="File uploaded",
        body=workspace_file.display_name,
        object_type="workspace_file",
        object_id=workspace_file.id,
        metadata={
            "file_name": workspace_file.display_name,
            "size_bytes": workspace_file.size_bytes,
        },
    )


def notify_github_repository_linked(
    *,
    workspace,
    actor,
    linked_repository,
):
    notifications = []

    for recipient in _workspace_contributor_users(
        workspace=workspace,
    ):
        notification = create_notification(
            recipient=recipient,
            actor=actor,
            workspace=workspace,
            notification_type=(
                Notification.Type.GITHUB_REPOSITORY_LINKED
            ),
            category=Notification.Category.GITHUB,
            title="GitHub repository linked",
            body=linked_repository.full_name,
            object_type="github_repository",
            object_id=linked_repository.github_repository_id,
            metadata={
                "repository": linked_repository.full_name,
                "primary": linked_repository.is_primary,
            },
            deduplication_key=(
                "github.repository_linked:"
                f"{workspace.id}:"
                f"{linked_repository.github_repository_id}"
            ),
        )

        if notification is not None:
            notifications.append(notification)

    return notifications
