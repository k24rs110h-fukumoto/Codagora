from rest_framework import serializers

from profiles.serializers import (
    PublicDeveloperProfileSerializer,
)

from .models import (
    CommunityPost,
    ExploreEvent,
    ExploreProject,
)


class ExploreProjectSerializer(
    serializers.ModelSerializer
):
    owner = serializers.SerializerMethodField()
    workspace = serializers.SerializerMethodField()

    class Meta:
        model = ExploreProject

        fields = (
            "id",
            "owner",
            "workspace",
            "title",
            "summary",
            "description",
            "status",
            "recruitment_status",
            "tags",
            "tech_stack",
            "wanted_roles",
            "repository_url",
            "website_url",
            "cover_image_url",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
        )

    def get_owner(
        self,
        obj,
    ):
        return {
            "id": str(
                obj.owner.id
            ),
            "display_name": (
                obj.owner.display_name
            ),
            "handle": (
                obj.owner.handle
            ),
            "avatar_url": (
                obj.owner.avatar_url
            ),
        }

    def get_workspace(
        self,
        obj,
    ):
        if obj.workspace is None:
            return None

        return {
            "id": str(
                obj.workspace.id
            ),
            "slug": (
                obj.workspace.slug
            ),
            "name": (
                obj.workspace.name
            ),
        }


class ExploreProjectWriteSerializer(
    serializers.Serializer
):
    workspace_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    title = serializers.CharField(
        max_length=120,
        required=False,
    )

    summary = serializers.CharField(
        max_length=300,
        required=False,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    status = serializers.ChoiceField(
        choices=ExploreProject.Status.choices,
        required=False,
    )

    recruitment_status = serializers.ChoiceField(
        choices=(
            ExploreProject
            .RecruitmentStatus
            .choices
        ),
        required=False,
    )

    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    tech_stack = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    wanted_roles = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    repository_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    website_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    cover_image_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    is_published = serializers.BooleanField(
        required=False,
    )


class CommunityPostSerializer(
    serializers.ModelSerializer
):
    author = serializers.SerializerMethodField()

    project = ExploreProjectSerializer(
        read_only=True,
    )

    class Meta:
        model = CommunityPost

        fields = (
            "id",
            "author",
            "project",
            "kind",
            "title",
            "body",
            "tags",
            "created_at",
            "updated_at",
        )

    def get_author(
        self,
        obj,
    ):
        return {
            "id": str(
                obj.author.id
            ),
            "display_name": (
                obj.author.display_name
            ),
            "handle": (
                obj.author.handle
            ),
            "avatar_url": (
                obj.author.avatar_url
            ),
        }


class CommunityPostWriteSerializer(
    serializers.Serializer
):
    project_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    kind = serializers.ChoiceField(
        choices=CommunityPost.Kind.choices,
        required=False,
    )

    title = serializers.CharField(
        max_length=160,
        required=False,
    )

    body = serializers.CharField(
        required=False,
    )

    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )


class ExploreEventSerializer(
    serializers.ModelSerializer
):
    organizer = serializers.SerializerMethodField()

    class Meta:
        model = ExploreEvent

        fields = (
            "id",
            "organizer",
            "title",
            "summary",
            "description",
            "starts_at",
            "ends_at",
            "location_name",
            "online_url",
            "tags",
            "capacity",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
        )

    def get_organizer(
        self,
        obj,
    ):
        return {
            "id": str(
                obj.organizer.id
            ),
            "display_name": (
                obj.organizer.display_name
            ),
            "handle": (
                obj.organizer.handle
            ),
            "avatar_url": (
                obj.organizer.avatar_url
            ),
        }


class ExploreEventWriteSerializer(
    serializers.Serializer
):
    title = serializers.CharField(
        max_length=160,
        required=False,
    )

    summary = serializers.CharField(
        max_length=300,
        required=False,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    starts_at = serializers.DateTimeField(
        required=False,
    )

    ends_at = serializers.DateTimeField(
        required=False,
    )

    location_name = serializers.CharField(
        max_length=160,
        required=False,
        allow_blank=True,
    )

    online_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )

    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    capacity = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )

    is_published = serializers.BooleanField(
        required=False,
    )