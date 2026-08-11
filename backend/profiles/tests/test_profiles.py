from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase

from profiles.models import (
    DeveloperProfile,
)
from profiles.selectors import (
    get_public_profile_by_handle,
    get_public_profiles,
)
from profiles.services import (
    get_or_create_developer_profile,
    update_developer_profile,
)


User = get_user_model()


class DeveloperProfileTests(
    TestCase
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="TestPassword123!",
        )

        self.user.display_name = (
            "Profile User"
        )

        self.user.handle = (
            "profile-user"
        )

        self.user.save()

    def test_profile_created_lazily(
        self,
    ):
        profile = (
            get_or_create_developer_profile(
                user=self.user,
            )
        )

        self.assertEqual(
            profile.user,
            self.user,
        )

        self.assertEqual(
            DeveloperProfile.objects.count(),
            1,
        )

    def test_profile_is_private_by_default(
        self,
    ):
        profile = (
            get_or_create_developer_profile(
                user=self.user,
            )
        )

        self.assertFalse(
            profile.is_public
        )

    def test_private_profile_not_discoverable(
        self,
    ):
        get_or_create_developer_profile(
            user=self.user,
        )

        self.assertEqual(
            get_public_profiles().count(),
            0,
        )

    def test_public_profile_is_discoverable(
        self,
    ):
        update_developer_profile(
            user=self.user,
            data={
                "headline": (
                    "iOS Developer"
                ),
                "is_public": True,
            },
        )

        self.assertEqual(
            get_public_profiles().count(),
            1,
        )

    def test_public_profile_found_by_handle(
        self,
    ):
        update_developer_profile(
            user=self.user,
            data={
                "is_public": True,
            },
        )

        profile = (
            get_public_profile_by_handle(
                handle="profile-user",
            )
        )

        self.assertIsNotNone(
            profile
        )

        self.assertEqual(
            profile.user,
            self.user,
        )

    def test_skills_are_normalized(
        self,
    ):
        profile = (
            update_developer_profile(
                user=self.user,
                data={
                    "skills": [
                        "Swift",
                        "swift",
                        "Django",
                        "",
                    ],
                },
            )
        )

        self.assertEqual(
            profile.skills,
            [
                "Swift",
                "Django",
            ],
        )

    def test_profile_update(
        self,
    ):
        profile = (
            update_developer_profile(
                user=self.user,
                data={
                    "headline": (
                        "Mobile Developer"
                    ),
                    "bio": (
                        "Building applications."
                    ),
                    "availability": (
                        DeveloperProfile
                        .Availability
                        .OPEN_TO_PROJECTS
                    ),
                    "location_label": (
                        "Fukuoka"
                    ),
                    "looking_for": [
                        "iOS",
                        "Team Development",
                    ],
                },
            )
        )

        self.assertEqual(
            profile.headline,
            "Mobile Developer",
        )

        self.assertEqual(
            profile.availability,
            DeveloperProfile
            .Availability
            .OPEN_TO_PROJECTS,
        )

        self.assertEqual(
            profile.location_label,
            "Fukuoka",
        )

        self.assertEqual(
            profile.looking_for,
            [
                "iOS",
                "Team Development",
            ],
        )