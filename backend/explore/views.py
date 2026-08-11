from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from profiles.models import DeveloperProfile
from profiles.serializers import (
    PublicDeveloperProfileSerializer,
)

from .models import (
    CommunityPost,
    ExploreEvent,
    ExploreProject,
)
from .pagination import ExplorePagination
from .selectors import (
    get_explore_overview,
    get_public_community_posts,
    get_public_events,
    get_public_people,
    get_public_projects,
)
from .serializers import (
    CommunityPostSerializer,
    CommunityPostWriteSerializer,
    ExploreEventSerializer,
    ExploreEventWriteSerializer,
    ExploreProjectSerializer,
    ExploreProjectWriteSerializer,
)
from .services import (
    create_community_post,
    create_explore_event,
    create_explore_project,
    delete_community_post,
    delete_explore_event,
    delete_explore_project,
    update_community_post,
    update_explore_event,
    update_explore_project,
)


class ExploreOverviewView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        data = get_explore_overview(
            user=request.user,
        )

        return Response(
            {
                "projects": (
                    ExploreProjectSerializer(
                        data["projects"],
                        many=True,
                    ).data
                ),
                "recruiting_projects": (
                    ExploreProjectSerializer(
                        data[
                            "recruiting_projects"
                        ],
                        many=True,
                    ).data
                ),
                "community": (
                    CommunityPostSerializer(
                        data["community"],
                        many=True,
                    ).data
                ),
                "people": (
                    PublicDeveloperProfileSerializer(
                        data["people"],
                        many=True,
                    ).data
                ),
                "events": (
                    ExploreEventSerializer(
                        data["events"],
                        many=True,
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )


class ProjectListCreateView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        queryset = get_public_projects(
            query=(
                request.query_params.get(
                    "q"
                )
            ),
            recruitment_only=(
                request.query_params.get(
                    "recruiting"
                )
                in (
                    "1",
                    "true",
                    "True",
                )
            ),
        )

        paginator = ExplorePagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = ExploreProjectSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(
        self,
        request,
    ):
        serializer = (
            ExploreProjectWriteSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        project = create_explore_project(
            actor=request.user,
            data=dict(
                serializer.validated_data
            ),
        )

        return Response(
            ExploreProjectSerializer(
                project
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_project(
        self,
        project_id,
    ):
        return get_object_or_404(
            ExploreProject,
            id=project_id,
        )

    def get(
        self,
        request,
        project_id,
    ):
        project = self.get_project(
            project_id
        )

        if (
            not project.is_published
            and project.owner_id
            != request.user.id
        ):
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            ExploreProjectSerializer(
                project
            ).data
        )

    def patch(
        self,
        request,
        project_id,
    ):
        project = self.get_project(
            project_id
        )

        serializer = (
            ExploreProjectWriteSerializer(
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        project = update_explore_project(
            project=project,
            actor=request.user,
            data=dict(
                serializer.validated_data
            ),
        )

        return Response(
            ExploreProjectSerializer(
                project
            ).data
        )

    def delete(
        self,
        request,
        project_id,
    ):
        project = self.get_project(
            project_id
        )

        delete_explore_project(
            project=project,
            actor=request.user,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class PeopleListView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        availability = (
            request.query_params.get(
                "availability"
            )
        )

        if (
            availability
            and availability
            not in DeveloperProfile
            .Availability
            .values
        ):
            return Response(
                {
                    "availability": [
                        "Invalid availability."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = get_public_people(
            query=(
                request.query_params.get(
                    "q"
                )
            ),
            availability=availability,
        )

        paginator = ExplorePagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = (
            PublicDeveloperProfileSerializer(
                page,
                many=True,
            )
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class CommunityListCreateView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        queryset = get_public_community_posts(
            query=(
                request.query_params.get(
                    "q"
                )
            ),
            kind=(
                request.query_params.get(
                    "kind"
                )
            ),
        )

        paginator = ExplorePagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = CommunityPostSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(
        self,
        request,
    ):
        serializer = (
            CommunityPostWriteSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        post = create_community_post(
            actor=request.user,
            data=dict(
                serializer.validated_data
            ),
        )

        return Response(
            CommunityPostSerializer(
                post
            ).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityDetailView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_post(
        self,
        post_id,
    ):
        return get_object_or_404(
            CommunityPost,
            id=post_id,
            deleted_at__isnull=True,
        )

    def get(
        self,
        request,
        post_id,
    ):
        post = self.get_post(
            post_id
        )

        if (
            not post.is_published
            and post.author_id
            != request.user.id
        ):
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            CommunityPostSerializer(
                post
            ).data
        )

    def patch(
        self,
        request,
        post_id,
    ):
        post = self.get_post(
            post_id
        )

        serializer = (
            CommunityPostWriteSerializer(
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        post = update_community_post(
            post=post,
            actor=request.user,
            data=dict(
                serializer.validated_data
            ),
        )

        return Response(
            CommunityPostSerializer(
                post
            ).data
        )

    def delete(
        self,
        request,
        post_id,
    ):
        post = self.get_post(
            post_id
        )

        delete_community_post(
            post=post,
            actor=request.user,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class EventListCreateView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        queryset = get_public_events(
            query=(
                request.query_params.get(
                    "q"
                )
            ),
        )

        paginator = ExplorePagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = ExploreEventSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(
        self,
        request,
    ):
        serializer = (
            ExploreEventWriteSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = create_explore_event(
            actor=request.user,
            data=dict(
                serializer.validated_data
            ),
        )

        return Response(
            ExploreEventSerializer(
                event
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EventDetailView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get_event(
        self,
        event_id,
    ):
        return get_object_or_404(
            ExploreEvent,
            id=event_id,
            deleted_at__isnull=True,
        )

    def get(
        self,
        request,
        event_id,
    ):
        event = self.get_event(
            event_id
        )

        if (
            not event.is_published
            and event.organizer_id
            != request.user.id
        ):
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            ExploreEventSerializer(
                event
            ).data
        )

    def patch(
        self,
        request,
        event_id,
    ):
        event = self.get_event(
            event_id
        )

        serializer = (
            ExploreEventWriteSerializer(
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = update_explore_event(
            event=event,
            actor=request.user,
            data=dict(
                serializer.validated_data
            ),
        )

        return Response(
            ExploreEventSerializer(
                event
            ).data
        )

    def delete(
        self,
        request,
        event_id,
    ):
        event = self.get_event(
            event_id
        )

        delete_explore_event(
            event=event,
            actor=request.user,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )