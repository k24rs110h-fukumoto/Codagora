from datetime import datetime, time, timedelta
from math import ceil
from zoneinfo import ZoneInfo

from .models import RecurrenceFrequency


def get_event_base_date(event):
    if event.is_all_day:
        return event.start_date

    timezone_info = ZoneInfo(
        event.timezone
    )

    return (
        event.starts_at
        .astimezone(timezone_info)
        .date()
    )


def get_event_span_days(event):
    if event.is_all_day:
        return (
            event.end_date
            - event.start_date
        ).days

    duration = (
        event.ends_at
        - event.starts_at
    )

    return max(
        1,
        ceil(
            duration.total_seconds()
            / 86400
        ),
    )


def matches_recurrence(
    *,
    event,
    candidate_date,
):
    base_date = get_event_base_date(
        event
    )

    if candidate_date < base_date:
        return False

    if (
        event.recurrence_until
        and candidate_date
        > event.recurrence_until
    ):
        return False

    frequency = (
        event.recurrence_frequency
    )

    interval = (
        event.recurrence_interval
        or 1
    )

    if (
        frequency
        == RecurrenceFrequency.NONE
    ):
        return (
            candidate_date
            == base_date
        )

    if (
        frequency
        == RecurrenceFrequency.DAILY
    ):
        difference = (
            candidate_date
            - base_date
        ).days

        return (
            difference % interval
            == 0
        )

    if (
        frequency
        == RecurrenceFrequency.WEEKLY
    ):
        base_week = (
            base_date
            - timedelta(
                days=base_date.weekday()
            )
        )

        candidate_week = (
            candidate_date
            - timedelta(
                days=(
                    candidate_date
                    .weekday()
                )
            )
        )

        weeks = (
            (
                candidate_week
                - base_week
            ).days
            // 7
        )

        weekdays = set(
            event.recurrence_weekdays
            or [
                base_date.weekday()
            ]
        )

        return (
            weeks >= 0
            and weeks % interval == 0
            and candidate_date.weekday()
            in weekdays
        )

    if (
        frequency
        == RecurrenceFrequency.MONTHLY
    ):
        months = (
            (
                candidate_date.year
                - base_date.year
            )
            * 12
            + (
                candidate_date.month
                - base_date.month
            )
        )

        return (
            months >= 0
            and months % interval == 0
            and candidate_date.day
            == base_date.day
        )

    return False


def build_occurrence(
    *,
    event,
    occurrence_date,
):
    if event.is_all_day:
        duration = (
            event.end_date
            - event.start_date
        )

        occurrence_end = (
            occurrence_date
            + duration
        )

        return {
            "event": event,
            "occurrence_key": (
                f"{event.id}:"
                f"{occurrence_date.isoformat()}"
            ),
            "is_all_day": True,
            "start_date": (
                occurrence_date
            ),
            "end_date": (
                occurrence_end
            ),
            "starts_at": None,
            "ends_at": None,
        }

    timezone_info = ZoneInfo(
        event.timezone
    )

    base_local = (
        event.starts_at
        .astimezone(
            timezone_info
        )
    )

    occurrence_start = datetime.combine(
        occurrence_date,
        time(
            hour=base_local.hour,
            minute=base_local.minute,
            second=base_local.second,
            microsecond=(
                base_local.microsecond
            ),
            tzinfo=timezone_info,
        ),
    )

    duration = (
        event.ends_at
        - event.starts_at
    )

    occurrence_end = (
        occurrence_start
        + duration
    )

    return {
        "event": event,
        "occurrence_key": (
            f"{event.id}:"
            f"{occurrence_start.isoformat()}"
        ),
        "is_all_day": False,
        "start_date": None,
        "end_date": None,
        "starts_at": (
            occurrence_start
        ),
        "ends_at": (
            occurrence_end
        ),
    }


def occurrence_overlaps_range(
    *,
    occurrence,
    range_start,
    range_end,
):
    if occurrence[
        "is_all_day"
    ]:
        return (
            occurrence[
                "start_date"
            ]
            <= range_end
            and occurrence[
                "end_date"
            ]
            >= range_start
        )

    event = occurrence["event"]

    timezone_info = ZoneInfo(
        event.timezone
    )

    range_start_datetime = (
        datetime.combine(
            range_start,
            time.min,
            tzinfo=timezone_info,
        )
    )

    range_end_datetime = (
        datetime.combine(
            range_end
            + timedelta(days=1),
            time.min,
            tzinfo=timezone_info,
        )
    )

    return (
        occurrence["starts_at"]
        < range_end_datetime
        and occurrence["ends_at"]
        > range_start_datetime
    )


def expand_event_occurrences(
    *,
    event,
    range_start,
    range_end,
):
    base_date = get_event_base_date(
        event
    )

    span_days = (
        get_event_span_days(event)
    )

    scan_start = max(
        base_date,
        range_start
        - timedelta(
            days=span_days
        ),
    )

    results = []

    candidate = scan_start

    while candidate <= range_end:
        if matches_recurrence(
            event=event,
            candidate_date=candidate,
        ):
            occurrence = (
                build_occurrence(
                    event=event,
                    occurrence_date=(
                        candidate
                    ),
                )
            )

            if occurrence_overlaps_range(
                occurrence=occurrence,
                range_start=range_start,
                range_end=range_end,
            ):
                results.append(
                    occurrence
                )

        candidate += timedelta(
            days=1
        )

    return results


def expand_events(
    *,
    events,
    range_start,
    range_end,
):
    occurrences = []

    for event in events:
        occurrences.extend(
            expand_event_occurrences(
                event=event,
                range_start=range_start,
                range_end=range_end,
            )
        )

    def sort_key(item):
        if item["is_all_day"]:
            return (
                item["start_date"],
                0,
                "",
            )

        local_start = (
            item["starts_at"]
            .astimezone(
                ZoneInfo(
                    item[
                        "event"
                    ].timezone
                )
            )
        )

        return (
            local_start.date(),
            1,
            local_start.isoformat(),
        )

    occurrences.sort(
        key=sort_key
    )

    return occurrences