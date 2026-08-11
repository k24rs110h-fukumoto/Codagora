from django.db.models import Q

from explore.models import ExploreProject

from .models import DeveloperProfile


def get_public_profiles(
    *,
    query=None,
    availability=None,
):
    queryset = (
        DeveloperProfile.objects
        .filter(
            is_public=True,
        )
        .select_related(
            "user",
        )
    )

    if availability:
        queryset = queryset.filter(
            availability=availability,
        )

    if query:
        query = query.strip()

        queryset = queryset.filter(
            Q(
                headline__icontains=query
            )
            | Q(
                bio__icontains=query
            )
            | Q(
                location_label__icontains=query
            )
            | Q(
                user__display_name__icontains=query
            )
            | Q(
                user__handle__icontains=query
            )
        )

    return queryset


def get_public_profile_by_handle(
    *,
    handle,
):
    return (
        DeveloperProfile.objects
        .filter(
            user__handle=handle,
            is_public=True,
        )
        .select_related(
            "user",
        )
        .first()
    )


def get_public_profile_projects(
    *,
    profile,
):
    if not profile.show_projects:
        return (
            ExploreProject.objects.none()
        )

    return (
        ExploreProject.objects
        .filter(
            owner=profile.user,
            is_published=True,
        )
        .select_related(
            "owner",
            "workspace",
        )
        .order_by(
            "-published_at",
            "-created_at",
        )
    )