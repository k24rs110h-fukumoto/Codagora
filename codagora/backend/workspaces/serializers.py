from django.utils import timezone

from rest_framework import serializers

from accounts.models import User

from .models import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
)


class WorkspaceUserSummarySerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = User

        fields = (
            "id",
            "display_name",
            "handle",
            "avatar_url",
        )

        read_only_fields = fields


class WorkspaceSerializer(
    serializers.ModelSerializer,
):
    owner = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    current_user_role = (
        serializers.SerializerMethodField()
    )

    active_member_count = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Workspace

        fields = (
            "id",
            "name",
            "slug",
            "description",
            "owner",
            "current_user_role",
            "active_member_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_current_user_role(
        self,
        obj,
    ):
        request = (
            self.context.get(
                "request"
            )
        )

        if not request:
            return None

        user = request.user

        if not user.is_authenticated:
            return None

        if obj.owner_id == user.id:
            return (
                WorkspaceMember.Role.OWNER
            )

        memberships = getattr(
            obj,
            "current_user_memberships",
            None,
        )

        if memberships is not None:
            if memberships:
                return (
                    memberships[0].role
                )

            return None

        membership = (
            WorkspaceMember.objects
            .filter(
                workspace=obj,
                user=user,
                is_active=True,
            )
            .first()
        )

        if not membership:
            return None

        return membership.role

    def get_active_member_count(
        self,
        obj,
    ):
        annotated = getattr(
            obj,
            "active_member_count",
            None,
        )

        if annotated is not None:
            return annotated

        return (
            obj.memberships
            .filter(
                is_active=True,
            )
            .count()
        )


class WorkspaceWriteSerializer(
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=100,
    )

    description = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            default="",
        )
    )

    def validate_name(
        self,
        value,
    ):
        normalized = value.strip()

        if not normalized:
            raise (
                serializers.ValidationError(
                    "Workspace名を"
                    "入力してください。"
                )
            )

        return normalized


class WorkspaceSummarySerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = Workspace

        fields = (
            "id",
            "name",
            "slug",
        )

        read_only_fields = fields


class WorkspaceMemberSerializer(
    serializers.ModelSerializer,
):
    user = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = WorkspaceMember

        fields = (
            "id",
            "user",
            "role",
            "is_active",
            "joined_at",
            "left_at",
            "updated_at",
        )

        read_only_fields = fields


class WorkspaceMembershipSerializer(
    serializers.ModelSerializer,
):
    workspace = (
        WorkspaceSummarySerializer(
            read_only=True,
        )
    )

    class Meta:
        model = WorkspaceMember

        fields = (
            "id",
            "workspace",
            "role",
            "is_active",
            "joined_at",
        )

        read_only_fields = fields


class WorkspaceMemberRoleUpdateSerializer(
    serializers.Serializer,
):
    role = serializers.ChoiceField(
        choices=(
            WorkspaceMember.Role.ADMIN,
            WorkspaceMember.Role.MEMBER,
            WorkspaceMember.Role.GUEST,
        ),
    )


class WorkspaceOwnershipTransferSerializer(
    serializers.Serializer,
):
    membership_id = (
        serializers.UUIDField()
    )


class WorkspaceInvitationSerializer(
    serializers.ModelSerializer,
):
    workspace = (
        WorkspaceSummarySerializer(
            read_only=True,
        )
    )

    created_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    revoked_by = (
        WorkspaceUserSummarySerializer(
            read_only=True,
        )
    )

    is_expired = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = WorkspaceInvitation

        fields = (
            "id",
            "workspace",
            "role",
            "created_by",
            "expires_at",
            "max_uses",
            "use_count",
            "is_active",
            "is_expired",
            "revoked_at",
            "revoked_by",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_is_expired(
        self,
        obj,
    ):
        return (
            obj.expires_at
            <= timezone.now()
        )


class WorkspaceInvitationCreateSerializer(
    serializers.Serializer,
):
    role = serializers.ChoiceField(
        choices=(
            WorkspaceInvitation.Role.ADMIN,
            WorkspaceInvitation.Role.MEMBER,
            WorkspaceInvitation.Role.GUEST,
        ),
        default=(
            WorkspaceInvitation.Role.MEMBER
        ),
    )

    expires_in_days = (
        serializers.IntegerField(
            min_value=1,
            max_value=30,
            default=7,
        )
    )

    max_uses = (
        serializers.IntegerField(
            min_value=1,
            max_value=100,
            default=1,
        )
    )


class WorkspaceInvitationCreatedSerializer(
    serializers.Serializer,
):
    id = serializers.UUIDField()

    workspace = (
        WorkspaceSummarySerializer()
    )

    role = serializers.CharField()

    expires_at = (
        serializers.DateTimeField()
    )

    max_uses = (
        serializers.IntegerField()
    )

    use_count = (
        serializers.IntegerField()
    )

    is_active = (
        serializers.BooleanField()
    )

    token = serializers.CharField()


class WorkspaceInvitationReissueSerializer(
    serializers.Serializer,
):
    expires_in_days = (
        serializers.IntegerField(
            min_value=1,
            max_value=30,
            default=7,
        )
    )

    max_uses = (
        serializers.IntegerField(
            min_value=1,
            max_value=100,
            required=False,
        )
    )


class WorkspaceInvitationAcceptSerializer(
    serializers.Serializer,
):
    token = serializers.CharField(
        max_length=512,
        trim_whitespace=True,
    )