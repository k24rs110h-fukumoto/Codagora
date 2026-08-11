from datetime import timedelta

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
)
from django.db.models import Q
from django.utils import timezone

from locations.models import (
    WorkspaceLocationShare,
)


class Command(BaseCommand):
    help = (
        "保持期間を過ぎた"
        "Workspace位置共有履歴を"
        "削除します。"
    )

    def handle(
        self,
        *args,
        **options,
    ):
        cutoff = (
            timezone.now()
            - timedelta(
                days=(
                    settings
                    .LOCATION_SHARE_HISTORY_RETENTION_DAYS
                )
            )
        )

        queryset = (
            WorkspaceLocationShare.objects
            .filter(
                Q(
                    ended_at__isnull=False,
                    ended_at__lte=cutoff,
                )
                | Q(
                    ended_at__isnull=True,
                    expires_at__lte=cutoff,
                )
            )
        )

        count = queryset.count()

        queryset.delete()

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Deleted "
                    f"{count} "
                    "location share record(s)."
                )
            )
        )