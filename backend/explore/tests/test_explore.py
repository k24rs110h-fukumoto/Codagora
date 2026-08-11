from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import (
    PermissionDenied,
)
from django.test import TestCase
from django.utils import timezone

from explore.models import (
    CommunityPost,
)
from explore.selectors import (
    get_public_people,
    get_public_projects,
)
from explore.services import (
    create_community_post,
    create_explore_event,
    create_explore_project,
)
from profiles.models import (
    DeveloperProfile,
)
from profiles.services import (
    update_developer_profile,
)
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)


User = get_user_model()


class ExploreServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="explore-owner@example.com",
            password="TestPassword123!",
        )

        self.owner.display_name = (
            "Explore Owner"
        )
        self.owner.handle = (
            "explore-owner"
        )
        self.owner.save()

        self.member = User.objects.create_user(
            email="explore-member@example.com",
            password="TestPassword123!",
        )

        self.member.display_name = (
            "Explore Member"
        )
        self.member.handle = (
            "explore-member"
        )
        self.member.save()

        self.workspace = (
            Workspace.objects.create(
                name="Explore Workspace",
                slug="explore-workspace",
                owner=self.owner,
            )
        )

        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.owner,
            defaults={
                "role": (
                    WorkspaceMember
                    .Role
                    .OWNER
                ),
                "is_active": True,
            },
        )

        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.member,
            role=(
                WorkspaceMember.Role.MEMBER
            ),
            is_active=True,
        )

    def test_owner_can_publish_project(
        self,
    ):
        project = create_explore_project(
            actor=self.owner,
            data={
                "workspace_id": (
                    self.workspace.id
                ),
                "title": "Codagora",
                "summary": (
                    "Developer platform"
                ),
                "is_published": True,
                "tags": [
                    "Swift",
                    "Django",
                ],
            },
        )

        self.assertTrue(
            project.is_published
        )

        self.assertIsNotNone(
            project.published_at
        )

    def test_member_cannot_publish_workspace_project(
        self,
    ):
        with self.assertRaises(
            PermissionDenied
        ):
            create_explore_project(
                actor=self.member,
                data={
                    "workspace_id": (
                        self.workspace.id
                    ),
                    "title": "Project",
                    "summary": "Test",
                    "is_published": True,
                },
            )

    def test_unpublished_project_not_in_explore(
        self,
    ):
        create_explore_project(
            actor=self.owner,
            data={
                "title": "Private Draft",
                "summary": "Draft",
                "is_published": False,
            },
        )

        self.assertEqual(
            get_public_projects().count(),
            0,
        )

    def test_published_project_is_in_explore(
        self,
    ):
        create_explore_project(
            actor=self.owner,
            data={
                "title": "Public Project",
                "summary": "Public",
                "is_published": True,
            },
        )

        self.assertEqual(
            get_public_projects().count(),
            1,
        )

    def test_profile_is_private_by_default(
        self,
    ):
        update_developer_profile(
            user=self.owner,
            data={
                "headline": (
                    "iOS Developer"
                ),
            },
        )

        self.assertEqual(
            get_public_people().count(),
            0,
        )

    def test_public_profile_appears_in_people(
        self,
    ):
        update_developer_profile(
            user=self.owner,
            data={
                "headline": (
                    "iOS Developer"
                ),
                "skills": [
                    "Swift",
                ],
                "is_public": True,
            },
        )

        people = get_public_people()

        self.assertEqual(
            people.count(),
            1,
        )

        self.assertEqual(
            people.first().user,
            self.owner,
        )

    def test_people_uses_profile_source_of_truth(
        self,
    ):
        profile = (
            update_developer_profile(
                user=self.owner,
                data={
                    "headline": (
                        "Mobile Developer"
                    ),
                    "availability": (
                        DeveloperProfile
                        .Availability
                        .OPEN_TO_PROJECTS
                    ),
                    "is_public": True,
                },
            )
        )

        person = (
            get_public_people().first()
        )

        self.assertEqual(
            person.id,
            profile.id,
        )

        self.assertEqual(
            person.headline,
            "Mobile Developer",
        )

    def test_people_availability_filter(
        self,
    ):
        update_developer_profile(
            user=self.owner,
            data={
                "availability": (
                    DeveloperProfile
                    .Availability
                    .OPEN_TO_PROJECTS
                ),
                "is_public": True,
            },
        )

        self.assertEqual(
            get_public_people(
                availability=(
                    DeveloperProfile
                    .Availability
                    .OPEN_TO_PROJECTS
                ),
            ).count(),
            1,
        )

        self.assertEqual(
            get_public_people(
                availability=(
                    DeveloperProfile
                    .Availability
                    .OPEN_TO_WORK
                ),
            ).count(),
            0,
        )

    def test_community_post(
        self,
    ):
        project = create_explore_project(
            actor=self.owner,
            data={
                "title": "Codagora",
                "summary": (
                    "Developer platform"
                ),
                "is_published": True,
            },
        )

        post = create_community_post(
            actor=self.owner,
            data={
                "project_id": (
                    project.id
                ),
                "kind": (
                    CommunityPost
                    .Kind
                    .PROJECT_RECRUITMENT
                ),
                "title": (
                    "iOS Developer募集"
                ),
                "body": (
                    "Codagoraを一緒に"
                    "開発するメンバー募集"
                ),
                "tags": [
                    "Swift",
                ],
            },
        )

        self.assertEqual(
            post.project,
            project,
        )

    def test_event_creation(
        self,
    ):
        start = (
            timezone.now()
            + timedelta(
                days=1
            )
        )

        event = create_explore_event(
            actor=self.owner,
            data={
                "title": (
                    "Codagora Meetup"
                ),
                "summary": (
                    "Developer meetup"
                ),
                "starts_at": start,
                "ends_at": (
                    start
                    + timedelta(
                        hours=2
                    )
                ),
                "is_published": True,
            },
        )

        self.assertTrue(
            event.is_published
        )

    def test_tag_duplicates_are_removed(
        self,
    ):
        project = create_explore_project(
            actor=self.owner,
            data={
                "title": "Project",
                "summary": "Test",
                "tags": [
                    "Swift",
                    "swift",
                    "Django",
                ],
            },
        )

        self.assertEqual(
            project.tags,
            [
                "Swift",
                "Django",
            ],
        )