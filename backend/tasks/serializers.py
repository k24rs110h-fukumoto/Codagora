from rest_framework import (
    serializers,
)

from workspaces.serializers import (
    WorkspaceUserSummarySerializer,
)

from .models import (
    Task,
    TaskComment,
    TaskPriority,
    TaskStatus,
)


class TaskSerializer(
    serializers.ModelSerializer,
):
    created_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    assignees = (
        serializers.SerializerMethodField()
    )

    comment_count = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Task

        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignees",
            "created_by",
            "due_at",
            "completed_at",
            "position",
            "comment_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_assignees(
        self,
        obj,
    ):
        prefetched = getattr(
            obj,
            "prefetched_assignees",
            None,
        )

        if prefetched is not None:
            users = [
                assignment.user
                for assignment
                in prefetched
            ]

        else:
            users = [
                assignment.user
                for assignment
                in obj.task_assignees
                .select_related(
                    "user",
                )
                .all()
            ]

        return (
            WorkspaceUserSummarySerializer(
                users,
                many=True,
            ).data
        )

    def get_comment_count(
        self,
        obj,
    ):
        count = getattr(
            obj,
            "active_comment_count",
            None,
        )

        if count is not None:
            return count

        return (
            obj.comments
            .filter(
                deleted_at__isnull=True,
            )
            .count()
        )


class TaskCreateSerializer(
    serializers.Serializer,
):
    title = serializers.CharField(
        max_length=160,
        trim_whitespace=True,
    )

    description = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            default="",
            trim_whitespace=True,
        )
    )

    status = serializers.ChoiceField(
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )

    priority = (
        serializers.ChoiceField(
            choices=(
                TaskPriority.choices
            ),
            default=(
                TaskPriority.MEDIUM
            ),
        )
    )

    assignee_ids = (
        serializers.ListField(
            child=(
                serializers.UUIDField()
            ),
            required=False,
            allow_empty=True,
            default=list,
        )
    )

    due_at = (
        serializers.DateTimeField(
            required=False,
            allow_null=True,
        )
    )

    def validate_assignee_ids(
        self,
        value,
    ):
        if len(value) != len(
            set(value)
        ):
            raise (
                serializers.ValidationError(
                    "担当者が重複しています。"
                )
            )

        return value


class TaskUpdateSerializer(
    serializers.Serializer,
):
    title = serializers.CharField(
        max_length=160,
        required=False,
        trim_whitespace=True,
    )

    description = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            trim_whitespace=True,
        )
    )

    status = serializers.ChoiceField(
        choices=TaskStatus.choices,
        required=False,
    )

    priority = (
        serializers.ChoiceField(
            choices=(
                TaskPriority.choices
            ),
            required=False,
        )
    )

    assignee_ids = (
        serializers.ListField(
            child=(
                serializers.UUIDField()
            ),
            required=False,
            allow_empty=True,
        )
    )

    due_at = (
        serializers.DateTimeField(
            required=False,
            allow_null=True,
        )
    )

    def validate_assignee_ids(
        self,
        value,
    ):
        if len(value) != len(
            set(value)
        ):
            raise (
                serializers.ValidationError(
                    "担当者が重複しています。"
                )
            )

        return value

    def validate(
        self,
        attrs,
    ):
        if not attrs:
            raise (
                serializers.ValidationError(
                    "変更する項目を"
                    "指定してください。"
                )
            )

        return attrs


class TaskFilterSerializer(
    serializers.Serializer,
):
    status = serializers.ChoiceField(
        choices=TaskStatus.choices,
        required=False,
    )

    priority = (
        serializers.ChoiceField(
            choices=(
                TaskPriority.choices
            ),
            required=False,
        )
    )

    assignee_id = (
        serializers.UUIDField(
            required=False,
        )
    )

    q = serializers.CharField(
        required=False,
        max_length=160,
        trim_whitespace=True,
    )

    overdue = (
        serializers.BooleanField(
            required=False,
        )
    )


class TaskReorderSerializer(
    serializers.Serializer,
):
    status = serializers.ChoiceField(
        choices=TaskStatus.choices,
    )

    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_task_ids(
        self,
        value,
    ):
        if len(value) != len(
            set(value)
        ):
            raise (
                serializers.ValidationError(
                    "Task IDが重複しています。"
                )
            )

        return value


class TaskCommentSerializer(
    serializers.ModelSerializer,
):
    author = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = TaskComment

        fields = (
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

class TaskCommentWriteSerializer(
    serializers.Serializer,
):
    content = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
    )