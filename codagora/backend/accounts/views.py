from django.contrib.auth import get_user_model
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserSkill
from .serializers import (
    CurrentUserSerializer,
    PublicProfileSerializer,
    UserSkillCreateSerializer,
    UserSkillSerializer,
    UserSkillUpdateSerializer,
    UserSummarySerializer,
)
from .services import (
    follow_user,
    set_user_skill,
    unfollow_user,
    update_user_skill_level,
)


User = get_user_model()


def raise_drf_validation_error(
    error: DjangoValidationError,
):
    if hasattr(error, "message_dict"):
        raise ValidationError(
            error.message_dict
        ) from error

    raise ValidationError(
        {
            "detail": error.messages,
        }
    ) from error


def get_public_profile(handle):
    return get_object_or_404(
        User.objects
        .filter(
            is_active=True,
            is_profile_public=True,
        )
        .prefetch_related(
            "user_skills__skill",
        ),
        handle__iexact=handle,
    )


class CurrentUserView(
    generics.RetrieveUpdateAPIView,
):
    serializer_class = CurrentUserSerializer

    permission_classes = (
        IsAuthenticated,
    )

    def get_object(self):
        return self.request.user


class PublicProfileView(
    generics.RetrieveAPIView,
):
    serializer_class = PublicProfileSerializer

    permission_classes = (
        IsAuthenticated,
    )

    def get_object(self):
        return get_public_profile(
            self.kwargs["handle"]
        )


class CurrentUserSkillListCreateView(
    APIView,
):
    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request):
        user_skills = (
            request.user.user_skills
            .select_related("skill")
            .order_by(
                "skill__name",
            )
        )

        serializer = UserSkillSerializer(
            user_skills,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        input_serializer = (
            UserSkillCreateSerializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        try:
            user_skill = set_user_skill(
                user=request.user,
                name=(
                    input_serializer
                    .validated_data["name"]
                ),
                level=(
                    input_serializer
                    .validated_data["level"]
                ),
            )
        except DjangoValidationError as error:
            raise_drf_validation_error(error)

        output_serializer = UserSkillSerializer(
            user_skill
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CurrentUserSkillDetailView(
    APIView,
):
    permission_classes = (
        IsAuthenticated,
    )

    def get_object(
        self,
        *,
        user,
        user_skill_id,
    ):
        return get_object_or_404(
            UserSkill.objects.select_related(
                "skill",
            ),
            id=user_skill_id,
            user=user,
        )

    def patch(
        self,
        request,
        user_skill_id,
    ):
        input_serializer = (
            UserSkillUpdateSerializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        user_skill = self.get_object(
            user=request.user,
            user_skill_id=user_skill_id,
        )

        try:
            user_skill = (
                update_user_skill_level(
                    user_skill=user_skill,
                    user=request.user,
                    level=(
                        input_serializer
                        .validated_data["level"]
                    ),
                )
            )
        except DjangoValidationError as error:
            raise_drf_validation_error(error)

        return Response(
            UserSkillSerializer(
                user_skill
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        user_skill_id,
    ):
        user_skill = self.get_object(
            user=request.user,
            user_skill_id=user_skill_id,
        )

        user_skill.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class FollowView(APIView):
    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request,
        handle,
    ):
        target = get_public_profile(handle)

        try:
            _, created = follow_user(
                follower=request.user,
                following=target,
            )
        except DjangoValidationError as error:
            raise_drf_validation_error(error)

        return Response(
            {
                "following": True,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )

    def delete(
        self,
        request,
        handle,
    ):
        target = get_public_profile(handle)

        unfollow_user(
            follower=request.user,
            following=target,
        )

        return Response(
            {
                "following": False,
            },
            status=status.HTTP_200_OK,
        )


class FollowersListView(
    generics.ListAPIView,
):
    serializer_class = UserSummarySerializer

    permission_classes = (
        IsAuthenticated,
    )

    def get_queryset(self):
        target = get_public_profile(
            self.kwargs["handle"]
        )

        return (
            User.objects
            .filter(
                following_relations__following=target,
                is_active=True,
                is_profile_public=True,
            )
            .distinct()
            .order_by("display_name")
        )


class FollowingListView(
    generics.ListAPIView,
):
    serializer_class = UserSummarySerializer

    permission_classes = (
        IsAuthenticated,
    )

    def get_queryset(self):
        target = get_public_profile(
            self.kwargs["handle"]
        )

        return (
            User.objects
            .filter(
                follower_relations__follower=target,
                is_active=True,
                is_profile_public=True,
            )
            .distinct()
            .order_by("display_name")
        )