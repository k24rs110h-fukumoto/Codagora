from django.urls import (
    include,
    path,
)

from .views import (
    WorkspaceDetailView,
    WorkspaceInvitationAcceptView,
    WorkspaceInvitationCreateView,
    WorkspaceInvitationReissueView,
    WorkspaceInvitationRevokeView,
    WorkspaceLeaveView,
    WorkspaceListCreateView,
    WorkspaceMemberDetailView,
    WorkspaceMemberListView,
    WorkspaceOwnershipTransferView,
)


app_name = "workspaces"


urlpatterns = [
    path(
        "invitations/accept/",
        WorkspaceInvitationAcceptView.as_view(),
        name="workspace-invitation-accept",
    ),

    path(
        "",
        WorkspaceListCreateView.as_view(),
        name="workspace-list-create",
    ),

    path(
        "<str:workspace_slug>/channels/",
        include("chat.urls"),
    ),

    path(
        "<str:workspace_slug>/tasks/",
        include("tasks.urls"),
    ),

    path(
        "<str:workspace_slug>/calendar/",
        include("scheduling.urls"),
    ),

    path(
        "<str:workspace_slug>/files/",
        include("workspace_files.urls"),
    ),

    path(
        "<str:workspace_slug>/map/",
        include("locations.urls"),
    ),

    path(
        "<str:workspace_slug>/github/",
        include("integrations.github_urls"),
    ),

    path(
        "<str:slug>/members/",
        WorkspaceMemberListView.as_view(),
        name="workspace-member-list",
    ),

    path(
        (
            "<str:slug>/members/"
            "<uuid:membership_id>/"
        ),
        WorkspaceMemberDetailView.as_view(),
        name="workspace-member-detail",
    ),

    path(
        "<str:slug>/leave/",
        WorkspaceLeaveView.as_view(),
        name="workspace-leave",
    ),

    path(
        "<str:slug>/ownership/transfer/",
        WorkspaceOwnershipTransferView.as_view(),
        name="workspace-transfer-ownership",
    ),

    path(
        "<str:slug>/invitations/",
        WorkspaceInvitationCreateView.as_view(),
        name="workspace-invitation-create",
    ),

    path(
        (
            "<str:slug>/invitations/"
            "<uuid:invitation_id>/revoke/"
        ),
        WorkspaceInvitationRevokeView.as_view(),
        name="workspace-invitation-revoke",
    ),

    path(
        (
            "<str:slug>/invitations/"
            "<uuid:invitation_id>/reissue/"
        ),
        WorkspaceInvitationReissueView.as_view(),
        name="workspace-invitation-reissue",
    ),

    path(
        "<str:slug>/",
        WorkspaceDetailView.as_view(),
        name="workspace-detail",
    ),
]