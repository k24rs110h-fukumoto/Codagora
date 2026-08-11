from django.db.models import Prefetch

from .models import (
    CalendarEvent,
    CalendarEventParticipant,
)


def get_workspace_calendar_events(
    *,
    workspace,
):
    participants = (
        CalendarEventParticipant
        .objects
        .select_related(
            "user",
        )
        .order_by(
            "created_at",
        )
    )

    return (
        CalendarEvent.objects
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
                "event_participants",
                queryset=participants,
                to_attr=(
                    "prefetched_participants"
                ),
            )
        )
        .order_by(
            "-updated_at",
        )
    )