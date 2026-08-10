from django.db.models import Q

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from .models import ActivityEvent


def get_workspace_role(
    *,
    workspace,
    user,
):
    if workspace.owner_id == user.id:
        return WorkspaceMember.Role.OWNER

    membership = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .first()
    )

    if membership is None:
        return None

    return membership.role


def _visible_events_for_role(
    queryset,
    role,
):
    if role in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
    ):
        return queryset

    if role == WorkspaceMember.Role.MEMBER:
        return queryset.filter(
            visibility__in=(
                ActivityEvent.Visibility.ALL_MEMBERS,
                ActivityEvent.Visibility.CONTRIBUTORS,
            )
        )

    if role == WorkspaceMember.Role.GUEST:
        return queryset.filter(
            visibility=(
                ActivityEvent.Visibility.ALL_MEMBERS
            )
        )

    return queryset.none()


def get_workspace_activity_events(
    *,
    workspace,
    viewer,
    category=None,
):
    role = get_workspace_role(
        workspace=workspace,
        user=viewer,
    )

    if role is None:
        return (
            ActivityEvent.objects.none()
        )

    queryset = (
        ActivityEvent.objects
        .filter(
            workspace=workspace,
        )
        .select_related(
            "workspace",
            "actor",
            "subject_user",
        )
    )

    queryset = _visible_events_for_role(
        queryset,
        role,
    )

    if category:
        queryset = queryset.filter(
            category=category,
        )

    return queryset


def get_personal_activity_events(
    *,
    user,
    category=None,
    workspace_slug=None,
):
    # Workspace.ownerはMembershipとは独立した
    # 正式なOwner判定として扱う
    owner_workspace_ids = set(
        Workspace.objects
        .filter(
            owner=user,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    memberships = (
        WorkspaceMember.objects
        .filter(
            user=user,
            is_active=True,
        )
        .values(
            "workspace_id",
            "role",
        )
    )

    manager_workspace_ids = set(
        owner_workspace_ids
    )

    contributor_workspace_ids = set()
    guest_workspace_ids = set()

    for membership in memberships:
        workspace_id = (
            membership["workspace_id"]
        )

        role = membership["role"]

        if role in (
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        ):
            manager_workspace_ids.add(
                workspace_id
            )

        elif (
            role
            == WorkspaceMember.Role.MEMBER
        ):
            contributor_workspace_ids.add(
                workspace_id
            )

        elif (
            role
            == WorkspaceMember.Role.GUEST
        ):
            guest_workspace_ids.add(
                workspace_id
            )

    queryset = (
        ActivityEvent.objects
        .filter(
            Q(actor=user)
            | Q(subject_user=user)
        )
        .filter(
            Q(workspace__isnull=True)
            | Q(
                workspace_id__in=(
                    manager_workspace_ids
                )
            )
            | Q(
                workspace_id__in=(
                    contributor_workspace_ids
                ),
                visibility__in=(
                    ActivityEvent.Visibility.ALL_MEMBERS,
                    ActivityEvent.Visibility.CONTRIBUTORS,
                ),
            )
            | Q(
                workspace_id__in=(
                    guest_workspace_ids
                ),
                visibility=(
                    ActivityEvent.Visibility.ALL_MEMBERS
                ),
            )
        )
        .select_related(
            "workspace",
            "actor",
            "subject_user",
        )
        .distinct()
    )

    if category:
        queryset = queryset.filter(
            category=category,
        )

    if workspace_slug:
        queryset = queryset.filter(
            workspace__slug=(
                workspace_slug
            ),
        )

    return queryset