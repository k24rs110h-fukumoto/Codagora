from django.contrib import admin

from .models import (
    CalendarEvent,
    CalendarEventParticipant,
)


class CalendarEventParticipantInline(
    admin.TabularInline,
):
    model = CalendarEventParticipant

    extra = 0

    autocomplete_fields = (
        "user",
        "added_by",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(CalendarEvent)
class CalendarEventAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "title",
        "workspace",
        "is_all_day",
        "recurrence_frequency",
        "created_by",
        "deleted_at",
        "updated_at",
    )

    list_filter = (
        "is_all_day",
        "recurrence_frequency",
        "deleted_at",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "location_name",
        "workspace__name",
        "workspace__slug",
        "created_by__email",
        "created_by__display_name",
    )

    autocomplete_fields = (
        "workspace",
        "created_by",
        "deleted_by",
    )

    readonly_fields = (
        "id",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )

    inlines = (
        CalendarEventParticipantInline,
    )


@admin.register(
    CalendarEventParticipant
)
class CalendarEventParticipantAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "event",
        "user",
        "response",
        "added_by",
        "updated_at",
    )

    list_filter = (
        "response",
    )

    search_fields = (
        "event__title",
        "user__email",
        "user__display_name",
    )

    autocomplete_fields = (
        "event",
        "user",
        "added_by",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )