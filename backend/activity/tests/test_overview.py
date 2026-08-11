from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.utils import timezone

from activity.models import (
    ActivityEvent,
)
from activity.overview import (
    build_activity_overview,
    build_activity_summary,
    build_portfolio_summary,
    build_skill_summary,
    build_workspace_contributions,
)
from activity.services import (
    record_activity_event,
)
from explore.models import (
    ExploreProject,
)
from profiles.models import (
    DeveloperProfile,
)
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)


User = get_user_model()


class ActivityOverviewTests(
    TestCase
):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email=(
                    "activity-overview@example.com"
                ),
                password=(
                    "TestPassword123!"
                ),
            )
        )

        self.user.display_name = (
            "Activity User"
        )

        self.user.handle = (
            "activity-user"
        )

        self.user.save()

        self.workspace = (
            Workspace.objects.create(
                name=(
                    "Activity Workspace"
                ),
                slug=(
                    "activity-workspace"
                ),
                owner=self.user,
            )
        )

        WorkspaceMember.objects.get_or_create(
            workspace=self.workspace,
            user=self.user,
            defaults={
                "role": (
                    WorkspaceMember
                    .Role
                    .OWNER
                ),
                "is_active": True,
            },
        )

    def test_overview_contains_all_sections(
        self,
    ):
        overview = (
            build_activity_overview(
                user=self.user,
            )
        )

        self.assertIn(
            "summary",
            overview,
        )

        self.assertIn(
            "skills",
            overview,
        )

        self.assertIn(
            "contributions",
            overview,
        )

        self.assertIn(
            "portfolio",
            overview,
        )

        self.assertIn(
            "career_signals",
            overview,
        )

        self.assertIn(
            "ai_insight",
            overview,
        )

        self.assertIn(
            "recent_activity",
            overview,
        )

    def test_completed_task_activity_is_counted(
        self,
    ):
        record_activity_event(
            workspace=self.workspace,
            actor=self.user,
            category=(
                ActivityEvent
                .Category
                .TASK
            ),
            event_type=(
                ActivityEvent
                .EventType
                .TASK_COMPLETED
            ),
            title="Task completed",
            object_type="task",
            object_id="task-1",
        )

        summary = (
            build_activity_summary(
                user=self.user,
            )
        )

        self.assertEqual(
            summary[
                "tasks_completed_30d"
            ],
            1,
        )

        self.assertEqual(
            summary[
                "events_30d"
            ],
            1,
        )

    def test_skills_merge_profile_and_projects(
        self,
    ):
        DeveloperProfile.objects.create(
            user=self.user,
            headline=(
                "iOS Developer"
            ),
            skills=[
                "Swift",
                "Django",
            ],
        )

        ExploreProject.objects.create(
            owner=self.user,
            title="Codagora",
            summary=(
                "Developer platform"
            ),
            tech_stack=[
                "Swift",
                "PostgreSQL",
            ],
        )

        skills = build_skill_summary(
            user=self.user,
        )

        names = {
            skill[
                "name"
            ]
            for skill in skills
        }

        self.assertIn(
            "Swift",
            names,
        )

        self.assertIn(
            "Django",
            names,
        )

        self.assertIn(
            "PostgreSQL",
            names,
        )

        swift = next(
            skill
            for skill in skills
            if (
                skill[
                    "name"
                ].lower()
                == "swift"
            )
        )

        self.assertTrue(
            swift[
                "profile_declared"
            ]
        )

        self.assertEqual(
            swift[
                "project_count"
            ],
            1,
        )

    def test_workspace_contribution(
        self,
    ):
        record_activity_event(
            workspace=self.workspace,
            actor=self.user,
            category=(
                ActivityEvent
                .Category
                .GITHUB
            ),
            event_type=(
                ActivityEvent
                .EventType
                .GITHUB_SYNCED
            ),
            title=(
                "GitHub synced"
            ),
            object_type=(
                "github_repository"
            ),
            object_id="123",
        )

        contributions = (
            build_workspace_contributions(
                user=self.user,
            )
        )

        self.assertEqual(
            len(
                contributions
            ),
            1,
        )

        contribution = (
            contributions[0]
        )

        self.assertEqual(
            contribution[
                "workspace"
            ][
                "slug"
            ],
            "activity-workspace",
        )

        self.assertEqual(
            contribution[
                "github"
            ],
            1,
        )

        self.assertEqual(
            contribution[
                "total_events"
            ],
            1,
        )

    def test_only_published_projects_in_portfolio(
        self,
    ):
        ExploreProject.objects.create(
            owner=self.user,
            title=(
                "Published"
            ),
            summary="Public",
            is_published=True,
            published_at=(
                timezone.now()
            ),
        )

        ExploreProject.objects.create(
            owner=self.user,
            title="Draft",
            summary="Private",
            is_published=False,
        )

        portfolio = (
            build_portfolio_summary(
                user=self.user,
            )
        )

        self.assertEqual(
            portfolio[
                "project_count"
            ],
            1,
        )

        self.assertEqual(
            portfolio[
                "projects"
            ][0][
                "title"
            ],
            "Published",
        )

    def test_ai_insight_is_not_faked(
        self,
    ):
        overview = (
            build_activity_overview(
                user=self.user,
            )
        )

        self.assertEqual(
            overview[
                "ai_insight"
            ][
                "status"
            ],
            "not_enabled",
        )

        self.assertIsNone(
            overview[
                "ai_insight"
            ][
                "summary"
            ]
        )