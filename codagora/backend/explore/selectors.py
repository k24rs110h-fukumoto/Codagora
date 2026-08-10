from django.db.models import Q
from django.utils import timezone

from profiles.models import DeveloperProfile

from .models import (
    CommunityPost,
    ExploreEvent,
    ExploreProject,
)


def get_public_projects(
    *,
    query=None,
    recruitment_only=False,
):
    queryset = (
        ExploreProject.objects
        .filter(
            is_published=True,
        )
        .select_related(
            "owner",
            "workspace",
        )
    )

    if recruitment_only:
        queryset = queryset.filter(
            recruitment_status=(
                ExploreProject
                .RecruitmentStatus
                .OPEN
            )
        )

    if query:
        query = query.strip()

        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(description__icontains=query)
            | Q(owner__display_name__icontains=query)
            | Q(owner__handle__icontains=query)
        )

    return queryset


def get_public_people(
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
            Q(headline__icontains=query)
            | Q(bio__icontains=query)
            | Q(location_label__icontains=query)
            | Q(user__display_name__icontains=query)
            | Q(user__handle__icontains=query)
        )

    return queryset


def get_public_community_posts(
    *,
    query=None,
    kind=None,
):
    queryset = (
        CommunityPost.objects
        .filter(
            is_published=True,
            deleted_at__isnull=True,
        )
        .select_related(
            "author",
            "project",
            "project__owner",
            "project__workspace",
        )
    )

    if kind:
        queryset = queryset.filter(
            kind=kind,
        )

    if query:
        query = query.strip()

        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(body__icontains=query)
            | Q(author__display_name__icontains=query)
            | Q(author__handle__icontains=query)
        )

    return queryset


def get_public_events(
    *,
    query=None,
    upcoming_only=True,
):
    queryset = (
        ExploreEvent.objects
        .filter(
            is_published=True,
            deleted_at__isnull=True,
        )
        .select_related(
            "organizer",
        )
    )

    if upcoming_only:
        queryset = queryset.filter(
            ends_at__gte=timezone.now(),
        )

    if query:
        query = query.strip()

        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(description__icontains=query)
            | Q(location_name__icontains=query)
            | Q(organizer__display_name__icontains=query)
            | Q(organizer__handle__icontains=query)
        )

    return queryset


def get_explore_overview(
    *,
    user,
):
    return {
        "projects": (
            get_public_projects()[:8]
        ),
        "recruiting_projects": (
            get_public_projects(
                recruitment_only=True,
            )[:8]
        ),
        "community": (
            get_public_community_posts()[:8]
        ),
        "people": (
            get_public_people()[:8]
        ),
        "events": (
            get_public_events()[:8]
        ),
    }