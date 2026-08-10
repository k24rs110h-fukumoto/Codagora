from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class ProfileApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="test-password-123",
            display_name="User",
            handle="user",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password-123",
            display_name="Other",
            handle="other",
        )

    def test_authenticated_user_can_get_me(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse("accounts:me"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

    def test_user_can_update_profile(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            reverse("accounts:me"),
            {
                "display_name": "Updated User",
                "handle": "Updated_User",
                "bio": "Codagora developer",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["handle"],
            "updated_user",
        )

    def test_user_can_add_skill(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "accounts:my-skill-list-create"
            ),
            {
                "name": "Swift",
                "level": 4,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["skill"]["name"],
            "Swift",
        )

        self.assertEqual(
            response.data["level"],
            4,
        )

    def test_public_profile_does_not_expose_email(
        self,
    ):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse(
                "accounts:profile-detail",
                kwargs={
                    "handle": self.other_user.handle,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertNotIn(
            "email",
            response.data,
        )

    def test_user_can_follow_other_user(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "accounts:profile-follow",
                kwargs={
                    "handle": self.other_user.handle,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        profile_response = self.client.get(
            reverse(
                "accounts:profile-detail",
                kwargs={
                    "handle": self.other_user.handle,
                },
            )
        )

        self.assertTrue(
            profile_response.data[
                "is_following"
            ]
        )

    def test_user_cannot_follow_self(self):
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "accounts:profile-follow",
                kwargs={
                    "handle": self.user.handle,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_private_profile_is_hidden(self):
        self.other_user.is_profile_public = False
        self.other_user.save(
            update_fields=(
                "is_profile_public",
            )
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse(
                "accounts:profile-detail",
                kwargs={
                    "handle": self.other_user.handle,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        