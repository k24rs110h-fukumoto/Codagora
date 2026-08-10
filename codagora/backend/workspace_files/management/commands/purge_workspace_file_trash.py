from datetime import timedelta

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
)
from django.utils import timezone

from workspace_files.models import (
    WorkspaceFile,
    WorkspaceFolder,
)


class Command(BaseCommand):
    help = (
        "保存期間を過ぎたWorkspace Filesの"
        "Trashを完全削除します。"
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
                    .WORKSPACE_FILE_TRASH_RETENTION_DAYS
                )
            )
        )

        deleted_files, _ = (
            WorkspaceFile.objects
            .filter(
                deleted_at__lte=cutoff,
            )
            .delete()
        )

        deleted_folders = 0

        while True:
            removed_this_pass = 0

            folders = list(
                WorkspaceFolder.objects
                .filter(
                    deleted_at__lte=cutoff,
                )
            )

            for folder in folders:
                if (
                    folder.children.exists()
                    or folder.files.exists()
                ):
                    continue

                folder.delete()

                removed_this_pass += 1
                deleted_folders += 1

            if removed_this_pass == 0:
                break

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Purged "
                    f"{deleted_files} file row(s) "
                    "and "
                    f"{deleted_folders} "
                    "folder(s)."
                )
            )
        )