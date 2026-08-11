from django.urls import path

from .views import (
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
    MarkNotificationUnreadView,
    NotificationListView,
    UnreadNotificationCountView,
)


app_name = "notifications"


urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="list",
    ),

    path(
        "unread-count/",
        UnreadNotificationCountView.as_view(),
        name="unread-count",
    ),

    path(
        "read-all/",
        MarkAllNotificationsReadView.as_view(),
        name="read-all",
    ),

    path(
        "<uuid:notification_id>/read/",
        MarkNotificationReadView.as_view(),
        name="read",
    ),

    path(
        "<uuid:notification_id>/unread/",
        MarkNotificationUnreadView.as_view(),
        name="unread",
    ),
]