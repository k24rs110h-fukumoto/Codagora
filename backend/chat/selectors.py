from .models import (
    Channel,
    Message,
)


def get_visible_channels(
    *,
    workspace,
):
    return (
        Channel.objects
        .filter(
            workspace=workspace,
            is_archived=False,
        )
        .select_related(
            "created_by",
        )
        .order_by(
            "position",
            "created_at",
        )
    )


def get_archived_channels(
    *,
    workspace,
):
    return (
        Channel.objects
        .filter(
            workspace=workspace,
            is_archived=True,
        )
        .select_related(
            "created_by",
            "archived_by",
        )
        .order_by(
            "-archived_at",
        )
    )


def get_channel_messages(
    *,
    channel,
):
    return (
        Message.objects
        .filter(
            channel=channel,
            deleted_at__isnull=True,
        )
        .select_related(
            "author",
            "reply_to",
            "reply_to__author",
        )
        .order_by(
            "-created_at",
        )
    )