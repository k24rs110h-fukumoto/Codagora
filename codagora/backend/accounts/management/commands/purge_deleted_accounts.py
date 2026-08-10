from django.core.management.base import (
    BaseCommand,
)
from django.db.models.deletion import (
    ProtectedError,
)
from django.utils import timezone

from firebase_admin import auth
from firebase_admin import (
    exceptions as firebase_exceptions,
)

from accounts.firebase import (
    get_firebase_app,
)
from accounts.models import (
    AccountStatus,
    User,
)


class Command(BaseCommand):
    help = (
        "削除猶予期間を過ぎた"
        "Codagoraアカウントを"
        "完全削除します。"
    )

    def handle(
        self,
        *args,
        **options,
    ):
        users = (
            User.objects
            .filter(
                account_status=(
                    AccountStatus
                    .DELETION_PENDING
                ),
                deletion_scheduled_for__lte=(
                    timezone.now()
                ),
            )
            .order_by(
                "deletion_scheduled_for"
            )
        )

        deleted_count = 0

        for user in users.iterator():
            firebase_uid = (
                user.firebase_uid
            )

            if user.owned_workspaces.exists():
                self.stderr.write(
                    (
                        f"SKIP {user.id}: "
                        "owned workspace exists"
                    )
                )
                continue

            if firebase_uid:
                try:
                    auth.delete_user(
                        firebase_uid,
                        app=get_firebase_app(),
                    )

                except auth.UserNotFoundError:
                    pass

                except (
                    firebase_exceptions
                    .FirebaseError
                ) as error:
                    self.stderr.write(
                        (
                            "Firebase delete "
                            f"failed {user.id}: "
                            f"{error}"
                        )
                    )
                    continue

            try:
                user.delete()

            except ProtectedError as error:
                self.stderr.write(
                    (
                        "Database delete "
                        f"blocked {user.id}: "
                        f"{error}"
                    )
                )
                continue

            deleted_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Deleted "
                    f"{deleted_count} "
                    "account(s)."
                )
            )
        )