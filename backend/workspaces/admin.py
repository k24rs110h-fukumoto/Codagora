from django.contrib import admin

from .models import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
)


class WorkspaceMemberInline(
    admin.TabularInline,
):
    model = WorkspaceMember

    extra = 0

    autocomplete_fields = (
        "user",
    )

    readonly_fields = (
        "id",
        "joined_at",
        "left_at",
        "updated_at",
    )


@admin.register(Workspace)
class WorkspaceAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "name",
        "slug",
        "owner",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "slug",
        "owner__email",
        "owner__display_name",
        "owner__handle",
    )

    autocomplete_fields = (
        "owner",
    )

    readonly_fields = (
        "id",
        "slug",
        "created_at",
        "updated_at",
    )

    inlines = (
        WorkspaceMemberInline,
    )


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "workspace",
        "user",
        "role",
        "is_active",
        "joined_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "workspace__name",
        "workspace__slug",
        "user__email",
        "user__display_name",
        "user__handle",
    )

    autocomplete_fields = (
        "workspace",
        "user",
    )

    readonly_fields = (
        "id",
        "joined_at",
        "left_at",
        "updated_at",
    )


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "workspace",
        "role",
        "created_by",
        "use_count",
        "max_uses",
        "is_active",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "workspace__name",
        "workspace__slug",
        "created_by__email",
    )

    autocomplete_fields = (
        "workspace",
        "created_by",
        "revoked_by",
    )

    readonly_fields = (
        "id",
        "token_hash",
        "use_count",
        "created_at",
        "updated_at",
        "revoked_at",
        "revoked_by",
    )