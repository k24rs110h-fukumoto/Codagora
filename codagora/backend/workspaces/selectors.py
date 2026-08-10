from django.db.models import (
    Case,
    Count,
    IntegerField,
    Prefetch,
    Q,
    Value,
    When,
)

from .models import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
)


def get_accessible_workspaces(
    *,
    user,
):
    current_memberships = (
        WorkspaceMember.objects
        .filter(
            user=user,
            is_active=True,
        )
        .select_related("user")
    )

    queryset = (
        Workspace.objects
        .select_related("owner")
        .annotate(
            active_member_count=Count(
                "memberships",
                filter=Q(
                    memberships__is_active=True
                ),
                distinct=True,
            )
        )
        .prefetch_related(
            Prefetch(
                "memberships",
                queryset=current_memberships,
                to_attr=(
                    "current_user_memberships"
                ),
            )
        )
    )

    if user.is_superuser:
        return queryset

    return queryset.filter(
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()


def get_active_workspace_members(
    *,
    workspace,
):
    role_order = Case(
        When(
            role=WorkspaceMember.Role.OWNER,
            then=Value(0),
        ),
        When(
            role=WorkspaceMember.Role.ADMIN,
            then=Value(1),
        ),
        When(
            role=WorkspaceMember.Role.MEMBER,
            then=Value(2),
        ),
        When(
            role=WorkspaceMember.Role.GUEST,
            then=Value(3),
        ),
        default=Value(4),
        output_field=IntegerField(),
    )

    return (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            is_active=True,
        )
        .select_related(
            "user",
            "workspace",
        )
        .annotate(
            role_order=role_order,
        )
        .order_by(
            "role_order",
            "joined_at",
        )
    )


def get_workspace_invitations(
    *,
    workspace,
):
    return (
        WorkspaceInvitation.objects
        .filter(
            workspace=workspace,
        )
        .select_related(
            "workspace",
            "created_by",
            "revoked_by",
        )
        .order_by(
            "-created_at",
        )
    )


def get_active_workspace_membership(
    *,
    workspace,
    user,
):
    return (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .first()
    )