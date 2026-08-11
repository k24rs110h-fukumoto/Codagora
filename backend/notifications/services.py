from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Notification


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


def _is_sensitive_key(
    key,
):
    normalized = str(
        key
    ).lower()

    return any(
        sensitive in normalized
        for sensitive
        in SENSITIVE_METADATA_KEYS
    )


def _sanitize_metadata(
    value,
):
    if isinstance(
        value,
        dict,
    ):
        result = {}

        for key, item in value.items():
            if _is_sensitive_key(
                key
            ):
                continue

            result[
                str(key)
            ] = _sanitize_metadata(
                item
            )

        return result

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _sanitize_metadata(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        UUID,
    ):
        return str(value)

    if isinstance(
        value,
        Decimal,
    ):
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
def create_notification(
    *,
    recipient,
    notification_type,
    category,
    title,
    actor=None,
    workspace=None,
    body="",
    object_type="",
    object_id="",
    metadata=None,
    deduplication_key=None,
):
    if (
        notification_type
        not in Notification.Type.values
    ):
        raise ValidationError(
            "Notification typeが不正です。"
        )

    if (
        category
        not in Notification.Category.values
    ):
        raise ValidationError(
            "Notification categoryが不正です。"
        )

    if (
        actor is not None
        and actor.id == recipient.id
    ):
        return None

    cleaned_metadata = (
        _sanitize_metadata(
            metadata or {}
        )
    )

    defaults = {
        "actor": actor,
        "workspace": workspace,
        "notification_type": (
            notification_type
        ),
        "category": category,
        "title": title,
        "body": body,
        "object_type": object_type,
        "object_id": str(
            object_id or ""
        ),
        "metadata": cleaned_metadata,
    }

    if deduplication_key:
        notification, _ = (
            Notification.objects
            .get_or_create(
                recipient=recipient,
                deduplication_key=(
                    deduplication_key
                ),
                defaults=defaults,
            )
        )

        return notification

    return Notification.objects.create(
        recipient=recipient,
        **defaults,
    )


@transaction.atomic
def create_notifications(
    *,
    recipients,
    notification_type,
    category,
    title,
    actor=None,
    workspace=None,
    body="",
    object_type="",
    object_id="",
    metadata=None,
):
    created = []

    recipient_ids = set()

    for recipient in recipients:
        if recipient.id in recipient_ids:
            continue

        recipient_ids.add(
            recipient.id
        )

        notification = (
            create_notification(
                recipient=recipient,
                actor=actor,
                workspace=workspace,
                notification_type=(
                    notification_type
                ),
                category=category,
                title=title,
                body=body,
                object_type=object_type,
                object_id=object_id,
                metadata=metadata,
            )
        )

        if notification is not None:
            created.append(
                notification
            )

    return created


@transaction.atomic
def mark_notification_as_read(
    *,
    notification,
    user,
):
    locked = (
        Notification.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=notification.id,
            recipient=user,
        )
        .first()
    )

    if locked is None:
        raise ValidationError(
            "Notificationが存在しません。"
        )

    if locked.read_at is not None:
        return locked

    locked.read_at = (
        timezone.now()
    )

    locked.save(
        update_fields=(
            "read_at",
        )
    )

    return locked


@transaction.atomic
def mark_notification_as_unread(
    *,
    notification,
    user,
):
    locked = (
        Notification.objects
        .select_for_update(
            of=("self",)
        )
        .filter(
            id=notification.id,
            recipient=user,
        )
        .first()
    )

    if locked is None:
        raise ValidationError(
            "Notificationが存在しません。"
        )

    if locked.read_at is None:
        return locked

    locked.read_at = None

    locked.save(
        update_fields=(
            "read_at",
        )
    )

    return locked


@transaction.atomic
def mark_all_notifications_as_read(
    *,
    user,
):
    now = timezone.now()

    return (
        Notification.objects
        .filter(
            recipient=user,
            read_at__isnull=True,
        )
        .update(
            read_at=now,
        )
    )