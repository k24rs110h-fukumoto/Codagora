from django.urls import path

from .views import (
    CalendarEventDetailView,
    CalendarEventListCreateView,
    CalendarOccurrenceListView,
    CalendarParticipantResponseView,
)


app_name = "scheduling"


urlpatterns = [
    path(
        "",
        CalendarEventListCreateView.as_view(),
        name="event-list-create",
    ),

    path(
        "occurrences/",
        CalendarOccurrenceListView.as_view(),
        name="occurrence-list",
    ),

    path(
        "<uuid:event_id>/",
        CalendarEventDetailView.as_view(),
        name="event-detail",
    ),

    path(
        "<uuid:event_id>/response/",
        CalendarParticipantResponseView.as_view(),
        name="participant-response",
    ),
]