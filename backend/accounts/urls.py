from django.urls import path

from .views import (
    CurrentUserSkillDetailView,
    CurrentUserSkillListCreateView,
    CurrentUserView,
    FollowersListView,
    FollowingListView,
    FollowView,
    PublicProfileView,
)


app_name = "accounts"


urlpatterns = [
    path(
        "me/",
        CurrentUserView.as_view(),
        name="me",
    ),

    path(
        "me/skills/",
        CurrentUserSkillListCreateView.as_view(),
        name="my-skill-list-create",
    ),

    path(
        "me/skills/<uuid:user_skill_id>/",
        CurrentUserSkillDetailView.as_view(),
        name="my-skill-detail",
    ),

    path(
        "profiles/<str:handle>/",
        PublicProfileView.as_view(),
        name="profile-detail",
    ),

    path(
        "profiles/<str:handle>/follow/",
        FollowView.as_view(),
        name="profile-follow",
    ),

    path(
        "profiles/<str:handle>/followers/",
        FollowersListView.as_view(),
        name="profile-followers",
    ),

    path(
        "profiles/<str:handle>/following/",
        FollowingListView.as_view(),
        name="profile-following",
    ),
]