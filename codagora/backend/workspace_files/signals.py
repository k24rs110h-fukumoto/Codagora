from django.db import transaction
from django.db.models.signals import (
    post_delete,
)
from django.dispatch import receiver

from .models import WorkspaceFile


@receiver(
    post_delete,
    sender=WorkspaceFile,
)
def delete_workspace_file_blob(
    sender,
    instance,
    **kwargs,
):
    if not instance.file:
        return

    file_name = (
        instance.file.name
    )

    if not file_name:
        return

    storage = (
        instance.file.storage
    )

    transaction.on_commit(
        lambda: storage.delete(
            file_name
        )
    )