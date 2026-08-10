from .models import Notification


def get_user_notifications(
    *,
    user,
    category=None,
    unread_only=False,
    workspace_slug=None,
):
    queryset = (
        Notification.objects
        .filter(
            recipient=user,
        )
        .select_related(
            "actor",
            "workspace",
        )
    )

    if category:
        queryset = queryset.filter(
            category=category,
        )

    if unread_only:
        queryset = queryset.filter(
            read_at__isnull=True,
        )

    if workspace_slug:
        queryset = queryset.filter(
            workspace__slug=(
                workspace_slug
            ),
        )

    return queryset


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