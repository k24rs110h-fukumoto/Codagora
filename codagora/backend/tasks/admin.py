from django.contrib import admin

from .models import (
    Task,
    TaskAssignee,
    TaskComment,
)


class TaskAssigneeInline(
    admin.TabularInline,
):
    model = TaskAssignee

    extra = 0

    autocomplete_fields = (
        "user",
        "assigned_by",
    )

    readonly_fields = (
        "id",
        "assigned_at",
    )


@admin.register(Task)
class TaskAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "title",
        "workspace",
        "status",
        "priority",
        "due_at",
        "created_by",
        "deleted_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "priority",
        "deleted_at",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "workspace__name",
        "workspace__slug",
        "created_by__email",
        "created_by__display_name",
    )

    autocomplete_fields = (
        "workspace",
        "created_by",
        "deleted_by",
    )

    readonly_fields = (
        "id",
        "completed_at",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )

    inlines = (
        TaskAssigneeInline,
    )


@admin.register(TaskAssignee)
class TaskAssigneeAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "task",
        "user",
        "assigned_by",
        "assigned_at",
    )

    search_fields = (
        "task__title",
        "user__email",
        "user__display_name",
    )

    autocomplete_fields = (
        "task",
        "user",
        "assigned_by",
    )

    readonly_fields = (
        "id",
        "assigned_at",
    )


@admin.register(TaskComment)
class TaskCommentAdmin(
    admin.ModelAdmin,
):
    list_display = (
        "task",
        "author",
        "deleted_at",
        "created_at",
    )

    search_fields = (
        "content",
        "task__title",
        "author__email",
        "author__display_name",
    )

    autocomplete_fields = (
        "task",
        "author",
        "deleted_by",
    )

    readonly_fields = (
        "id",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )