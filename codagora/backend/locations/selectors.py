from django.utils import timezone

from .models import (
    WorkspaceLocationShare,
    WorkspacePlace,
)


def get_workspace_places(
    *,
    workspace,
):
    return (
        WorkspacePlace.objects
        .filter(
            workspace=workspace,
            deleted_at__isnull=True,
        )
        .select_related(
            "created_by",
        )
        .order_by(
            "name",
            "created_at",
        )
    )


def get_active_location_shares(
    *,
    workspace,
):
    return (
        WorkspaceLocationShare.objects
        .filter(
            workspace=workspace,
            ended_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .select_related(
            "user",
            "place",
        )
        .order_by(
            "-updated_at",
        )
    )


def get_current_location_share(
    *,
    workspace,
    user,
):
    return (
        WorkspaceLocationShare.objects
        .filter(
            workspace=workspace,
            user=user,
            ended_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .select_related(
            "user",
            "place",
        )
        .first()
    )