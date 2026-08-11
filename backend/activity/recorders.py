from .models import ActivityEvent
from .services import record_activity_event


def record_workspace_created(
    *,
    workspace,
    actor,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.WORKSPACE,
        event_type=(
            ActivityEvent.EventType.WORKSPACE_CREATED
        ),
        title="Workspace created",
        object_type="workspace",
        object_id=workspace.id,
        metadata={
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
        },
    )


def record_workspace_member_joined(
    *,
    workspace,
    actor,
    member_user,
    role,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        subject_user=member_user,
        category=ActivityEvent.Category.WORKSPACE,
        event_type=(
            ActivityEvent.EventType
            .WORKSPACE_MEMBER_JOINED
        ),
        title="Workspace member joined",
        object_type="workspace_member",
        object_id=member_user.id,
        metadata={
            "role": role,
        },
    )


def record_channel_created(
    *,
    workspace,
    actor,
    channel,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.CHAT,
        event_type=(
            ActivityEvent.EventType.CHANNEL_CREATED
        ),
        title="Channel created",
        object_type="channel",
        object_id=channel.id,
        metadata={
            "channel_name": channel.name,
            "channel_type": channel.channel_type,
        },
    )


def record_message_sent(
    *,
    workspace,
    actor,
    message,
    channel,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.CHAT,
        event_type=(
            ActivityEvent.EventType.MESSAGE_SENT
        ),
        visibility=(
            ActivityEvent.Visibility.CONTRIBUTORS
        ),
        title="Message sent",
        object_type="message",
        object_id=message.id,
        metadata={
            "channel_id": str(channel.id),
            "channel_name": channel.name,
        },
    )


def record_task_created(
    *,
    workspace,
    actor,
    task,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.TASK,
        event_type=(
            ActivityEvent.EventType.TASK_CREATED
        ),
        title="Task created",
        object_type="task",
        object_id=task.id,
        metadata={
            "task_title": task.title,
            "status": task.status,
            "priority": task.priority,
        },
    )


def record_task_updated(
    *,
    workspace,
    actor,
    task,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.TASK,
        event_type=(
            ActivityEvent.EventType.TASK_UPDATED
        ),
        title="Task updated",
        object_type="task",
        object_id=task.id,
        metadata={
            "task_title": task.title,
            "status": task.status,
            "priority": task.priority,
        },
    )


def record_task_completed(
    *,
    workspace,
    actor,
    task,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.TASK,
        event_type=(
            ActivityEvent.EventType.TASK_COMPLETED
        ),
        title="Task completed",
        object_type="task",
        object_id=task.id,
        metadata={
            "task_title": task.title,
        },
    )


def record_calendar_created(
    *,
    workspace,
    actor,
    event,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.CALENDAR,
        event_type=(
            ActivityEvent.EventType.CALENDAR_CREATED
        ),
        title="Calendar event created",
        object_type="calendar_event",
        object_id=event.id,
        metadata={
            "title": event.title,
            "is_all_day": event.is_all_day,
        },
    )


def record_calendar_updated(
    *,
    workspace,
    actor,
    event,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.CALENDAR,
        event_type=(
            ActivityEvent.EventType.CALENDAR_UPDATED
        ),
        title="Calendar event updated",
        object_type="calendar_event",
        object_id=event.id,
        metadata={
            "title": event.title,
            "is_all_day": event.is_all_day,
        },
    )


def record_file_uploaded(
    *,
    workspace,
    actor,
    file_id,
    file_name,
    size_bytes=None,
):
    metadata = {
        "file_name": file_name,
    }

    if size_bytes is not None:
        metadata["size_bytes"] = size_bytes

    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.FILE,
        event_type=(
            ActivityEvent.EventType.FILE_UPLOADED
        ),
        title="File uploaded",
        object_type="workspace_file",
        object_id=file_id,
        metadata=metadata,
    )


def record_place_created(
    *,
    workspace,
    actor,
    place,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.MAP,
        event_type=(
            ActivityEvent.EventType.PLACE_CREATED
        ),
        title="Workspace place created",
        object_type="workspace_place",
        object_id=place.id,
        metadata={
            "place_name": place.name,
        },
    )


def record_github_repository_linked(
    *,
    workspace,
    actor,
    linked_repository,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.GITHUB,
        event_type=(
            ActivityEvent.EventType
            .GITHUB_REPOSITORY_LINKED
        ),
        source=ActivityEvent.Source.GITHUB,
        title="GitHub repository linked",
        object_type="github_repository",
        object_id=(
            linked_repository.github_repository_id
        ),
        metadata={
            "repository": (
                linked_repository.full_name
            ),
            "primary": (
                linked_repository.is_primary
            ),
        },
        deduplication_key=(
            "github.repository_linked:"
            f"{workspace.id}:"
            f"{linked_repository.github_repository_id}"
        ),
    )


def record_github_synced(
    *,
    workspace,
    actor,
    linked_repository,
):
    return record_activity_event(
        workspace=workspace,
        actor=actor,
        category=ActivityEvent.Category.GITHUB,
        event_type=(
            ActivityEvent.EventType.GITHUB_SYNCED
        ),
        source=ActivityEvent.Source.GITHUB,
        title="GitHub repository synced",
        object_type="github_repository",
        object_id=(
            linked_repository.github_repository_id
        ),
        metadata={
            "repository": (
                linked_repository.full_name
            ),
        },
    )