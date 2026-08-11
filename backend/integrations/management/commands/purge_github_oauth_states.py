from datetime import timedelta

from django.core.management.base import (
    BaseCommand,
)
from django.utils import timezone

from integrations.models import (
    GitHubOAuthState,
)


class Command(BaseCommand):
    help = (
        "古いGitHub OAuth Stateを"
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
                days=1
            )
        )

        queryset = (
            GitHubOAuthState.objects
            .filter(
                expires_at__lte=cutoff,
            )
        )

        count = queryset.count()

        queryset.delete()

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Deleted {count} "
                    "GitHub OAuth state(s)."
                )
            )
        )