from django.contrib import admin

from .models import (
    CommunityPost,
    ExploreEvent,
    ExploreProject,
)


@admin.register(ExploreProject)
class ExploreProjectAdmin(
    admin.ModelAdmin
):
    list_display = (
        "title",
        "owner",
        "status",
        "recruitment_status",
        "is_published",
        "published_at",
    )

    list_filter = (
        "status",
        "recruitment_status",
        "is_published",
    )

    search_fields = (
        "title",
        "summary",
        "owner__email",
        "owner__display_name",
        "owner__handle",
    )


@admin.register(CommunityPost)
class CommunityPostAdmin(
    admin.ModelAdmin
):
    list_display = (
        "title",
        "author",
        "kind",
        "is_published",
        "created_at",
    )

    list_filter = (
        "kind",
        "is_published",
    )

    search_fields = (
        "title",
        "body",
        "author__email",
        "author__display_name",
        "author__handle",
    )


@admin.register(ExploreEvent)
class ExploreEventAdmin(
    admin.ModelAdmin
):
    list_display = (
        "title",
        "organizer",
        "starts_at",
        "ends_at",
        "is_published",
    )

    list_filter = (
        "is_published",
    )

    search_fields = (
        "title",
        "summary",
        "organizer__email",
        "organizer__display_name",
        "organizer__handle",
    )