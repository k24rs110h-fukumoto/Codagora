from django.urls import path

from .views import (
    ArchivedChannelListView,
    ChannelArchiveView,
    ChannelDetailView,
    ChannelListCreateView,
    ChannelReorderView,
    ChannelRestoreView,
    MessageDetailView,
    MessageListCreateView,
)


app_name = "chat"


urlpatterns = [
    path(
        "",
        ChannelListCreateView.as_view(),
        name="channel-list-create",
    ),

    path(
        "archived/",
        ArchivedChannelListView.as_view(),
        name="channel-archived-list",
    ),

    path(
        "reorder/",
        ChannelReorderView.as_view(),
        name="channel-reorder",
    ),

    path(
        "<uuid:channel_id>/",
        ChannelDetailView.as_view(),
        name="channel-detail",
    ),

    path(
        "<uuid:channel_id>/archive/",
        ChannelArchiveView.as_view(),
        name="channel-archive",
    ),

    path(
        "<uuid:channel_id>/restore/",
        ChannelRestoreView.as_view(),
        name="channel-restore",
    ),

    path(
        "<uuid:channel_id>/messages/",
        MessageListCreateView.as_view(),
        name="message-list-create",
    ),

    path(
        (
            "<uuid:channel_id>/messages/"
            "<uuid:message_id>/"
        ),
        MessageDetailView.as_view(),
        name="message-detail",
    ),
]