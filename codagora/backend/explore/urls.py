from django.urls import path

from .views import (
    CommunityDetailView,
    CommunityListCreateView,
    EventDetailView,
    EventListCreateView,
    ExploreOverviewView,
    PeopleListView,
    ProjectDetailView,
    ProjectListCreateView,
)


app_name = "explore"


urlpatterns = [
    path(
        "",
        ExploreOverviewView.as_view(),
        name="overview",
    ),

    path(
        "projects/",
        ProjectListCreateView.as_view(),
        name="projects",
    ),

    path(
        "projects/<uuid:project_id>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),

    path(
        "community/",
        CommunityListCreateView.as_view(),
        name="community",
    ),

    path(
        "community/<uuid:post_id>/",
        CommunityDetailView.as_view(),
        name="community-detail",
    ),

    path(
        "people/",
        PeopleListView.as_view(),
        name="people",
    ),

    path(
        "events/",
        EventListCreateView.as_view(),
        name="events",
    ),

    path(
        "events/<uuid:event_id>/",
        EventDetailView.as_view(),
        name="event-detail",
    ),
]