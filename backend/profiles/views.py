from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import status
from rest_framework.response import (
    Response,
)
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from explore.serializers import (
    ExploreProjectSerializer,
)

from .models import DeveloperProfile
from .selectors import (
    get_public_profile_by_handle,
    get_public_profile_projects,
)
from .serializers import (
    DeveloperProfileSerializer,
    DeveloperProfileWriteSerializer,
    PublicDeveloperProfileSerializer,
)
from .services import (
    get_or_create_developer_profile,
    update_developer_profile,
)


class MyProfileView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
    ):
        profile = (
            get_or_create_developer_profile(
                user=request.user,
            )
        )

        return Response(
            DeveloperProfileSerializer(
                profile
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
    ):
        serializer = (
            DeveloperProfileWriteSerializer(
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        profile = (
            update_developer_profile(
                user=request.user,
                data=dict(
                    serializer.validated_data
                ),
            )
        )

        return Response(
            DeveloperProfileSerializer(
                profile
            ).data,
            status=status.HTTP_200_OK,
        )


class PublicProfileView(APIView):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        handle,
    ):
        if (
            request.user.handle
            == handle
        ):
            profile = (
                get_or_create_developer_profile(
                    user=request.user,
                )
            )

            return Response(
                DeveloperProfileSerializer(
                    profile
                ).data,
                status=status.HTTP_200_OK,
            )

        profile = (
            get_public_profile_by_handle(
                handle=handle,
            )
        )

        if profile is None:
            return Response(
                status=(
                    status.HTTP_404_NOT_FOUND
                )
            )

        return Response(
            PublicDeveloperProfileSerializer(
                profile
            ).data,
            status=status.HTTP_200_OK,
        )


class PublicProfileProjectsView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        handle,
    ):
        if (
            request.user.handle
            == handle
        ):
            profile = (
                get_or_create_developer_profile(
                    user=request.user,
                )
            )

        else:
            profile = (
                get_public_profile_by_handle(
                    handle=handle,
                )
            )

            if profile is None:
                return Response(
                    status=(
                        status.HTTP_404_NOT_FOUND
                    )
                )

        projects = (
            get_public_profile_projects(
                profile=profile,
            )
        )

        return Response(
            ExploreProjectSerializer(
                projects,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )