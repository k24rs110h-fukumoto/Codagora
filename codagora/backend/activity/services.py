from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ActivityEvent


SENSITIVE_METADATA_KEYS = (
    "token",
    "secret",
    "password",
    "authorization",
    "private_key",
    "privatekey",
    "access_token",
    "refresh_token",
)


def _is_sensitive_key(key):
    normalized = str(key).lower()

    return any(
        sensitive in normalized
        for sensitive in SENSITIVE_METADATA_KEYS
    )


def _sanitize_metadata(value):
    if isinstance(value, dict):
        result = {}

        for key, item in value.items():
            if _is_sensitive_key(key):
                continue

            result[str(key)] = (
                _sanitize_metadata(item)
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _sanitize_metadata(item)
            for item in value
        ]

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if value is None:
        return None

    return str(value)


@transaction.atomic
def record_activity_event(
    *,
    category,
    event_type,
    title,
    workspace=None,
    actor=None,
    subject_user=None,
    visibility=(
        ActivityEvent.Visibility.ALL_MEMBERS
    ),
    source=ActivityEvent.Source.INTERNAL,
    object_type="",
    object_id="",
    summary="",
    metadata=None,
    deduplication_key=None,
    occurred_at=None,
):
    if (
        workspace is None
        and actor is None
        and subject_user is None
    ):
        raise ValidationError(
            "Activity event must have a "
            "workspace, actor or subject user."
        )

    if category not in ActivityEvent.Category.values:
        raise ValidationError(
            "Invalid activity category."
        )

    if event_type not in ActivityEvent.EventType.values:
        raise ValidationError(
            "Invalid activity event type."
        )

    if (
        visibility
        not in ActivityEvent.Visibility.values
    ):
        raise ValidationError(
            "Invalid activity visibility."
        )

    if source not in ActivityEvent.Source.values:
        raise ValidationError(
            "Invalid activity source."
        )

    cleaned_metadata = (
        _sanitize_metadata(
            metadata or {}
        )
    )

    defaults = {
        "workspace": workspace,
        "actor": actor,
        "subject_user": subject_user,
        "category": category,
        "event_type": event_type,
        "visibility": visibility,
        "source": source,
        "object_type": object_type,
        "object_id": str(
            object_id or ""
        ),
        "title": title,
        "summary": summary,
        "metadata": cleaned_metadata,
    }

    if occurred_at is not None:
        defaults["occurred_at"] = (
            occurred_at
        )

    if deduplication_key:
        event, _ = (
            ActivityEvent.objects.get_or_create(
                deduplication_key=(
                    deduplication_key
                ),
                defaults=defaults,
            )
        )

        return event

    return ActivityEvent.objects.create(
        **defaults
    )