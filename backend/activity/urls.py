from django.urls import path

from .views import (
    ActivityOverviewView,
    PersonalActivityListView,
)


app_name = "activity"


urlpatterns = [
    path(
        "",
        PersonalActivityListView.as_view(),
        name="list",
    ),

    path(
        "overview/",
        ActivityOverviewView.as_view(),
        name="overview",
    ),
]