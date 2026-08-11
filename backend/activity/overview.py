from collections import defaultdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from explore.models import ExploreProject
from profiles.models import DeveloperProfile
from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from .models import ActivityEvent


def get_accessible_workspaces(
    *,
    user,
):
    membership_workspace_ids = (
        WorkspaceMember.objects
        .filter(
            user=user,
            is_active=True,
        )
        .values_list(
            "workspace_id",
            flat=True,
        )
    )

    return (
        Workspace.objects
        .filter(
            Q(owner=user)
            | Q(
                id__in=(
                    membership_workspace_ids
                )
            )
        )
        .distinct()
    )


def get_user_activity_events(
    *,
    user,
):
    return (
        ActivityEvent.objects
        .filter(
            actor=user,
        )
        .select_related(
            "workspace",
            "actor",
            "subject_user",
        )
        .order_by(
            "-occurred_at",
            "-created_at",
        )
    )


def build_activity_summary(
    *,
    user,
):
    now = timezone.now()

    since_30_days = (
        now
        - timedelta(
            days=30
        )
    )

    events = (
        get_user_activity_events(
            user=user,
        )
        .filter(
            occurred_at__gte=(
                since_30_days
            ),
        )
    )

    active_days = (
        events
        .dates(
            "occurred_at",
            "day",
        )
        .count()
    )

    completed_tasks = (
        events
        .filter(
            event_type=(
                ActivityEvent
                .EventType
                .TASK_COMPLETED
            )
        )
        .count()
    )

    github_events = (
        events
        .filter(
            category=(
                ActivityEvent
                .Category
                .GITHUB
            )
        )
        .count()
    )

    workspace_count = (
        get_accessible_workspaces(
            user=user,
        )
        .count()
    )

    published_projects = (
        ExploreProject.objects
        .filter(
            owner=user,
            is_published=True,
        )
        .count()
    )

    return {
        "events_30d": (
            events.count()
        ),
        "active_days_30d": (
            active_days
        ),
        "tasks_completed_30d": (
            completed_tasks
        ),
        "github_events_30d": (
            github_events
        ),
        "workspace_count": (
            workspace_count
        ),
        "published_projects": (
            published_projects
        ),
    }


def build_skill_summary(
    *,
    user,
):
    profile = (
        DeveloperProfile.objects
        .filter(
            user=user,
        )
        .first()
    )

    profile_skills = (
        profile.skills
        if profile
        else []
    )

    projects = (
        ExploreProject.objects
        .filter(
            owner=user,
        )
        .only(
            "tech_stack",
        )
    )

    skills = {}

    for skill in profile_skills:
        name = str(
            skill
        ).strip()

        if not name:
            continue

        key = name.lower()

        skills[key] = {
            "name": name,
            "profile_declared": True,
            "project_count": 0,
        }

    for project in projects:
        project_seen = set()

        for skill in (
            project.tech_stack
            or []
        ):
            name = str(
                skill
            ).strip()

            if not name:
                continue

            key = name.lower()

            if key in project_seen:
                continue

            project_seen.add(
                key
            )

            if key not in skills:
                skills[key] = {
                    "name": name,
                    "profile_declared": False,
                    "project_count": 0,
                }

            skills[
                key
            ][
                "project_count"
            ] += 1

    result = list(
        skills.values()
    )

    result.sort(
        key=lambda item: (
            not item[
                "profile_declared"
            ],
            -item[
                "project_count"
            ],
            item[
                "name"
            ].lower(),
        )
    )

    return result


def build_workspace_contributions(
    *,
    user,
):
    workspaces = list(
        get_accessible_workspaces(
            user=user,
        )
    )

    events = (
        get_user_activity_events(
            user=user,
        )
        .filter(
            workspace__in=(
                workspaces
            ),
        )
    )

    workspace_data = {}

    for workspace in workspaces:
        workspace_data[
            workspace.id
        ] = {
            "workspace": {
                "id": str(
                    workspace.id
                ),
                "slug": (
                    workspace.slug
                ),
                "name": (
                    workspace.name
                ),
            },
            "total_events": 0,
            "tasks": 0,
            "chat": 0,
            "calendar": 0,
            "files": 0,
            "github": 0,
            "map": 0,
            "workspace_events": 0,
            "tasks_completed": 0,
            "last_contributed_at": None,
        }

    for event in events:
        if event.workspace_id is None:
            continue

        contribution = (
            workspace_data.get(
                event.workspace_id
            )
        )

        if contribution is None:
            continue

        contribution[
            "total_events"
        ] += 1

        category_mapping = {
            ActivityEvent.Category.TASK: (
                "tasks"
            ),
            ActivityEvent.Category.CHAT: (
                "chat"
            ),
            ActivityEvent.Category.CALENDAR: (
                "calendar"
            ),
            ActivityEvent.Category.FILE: (
                "files"
            ),
            ActivityEvent.Category.GITHUB: (
                "github"
            ),
            ActivityEvent.Category.MAP: (
                "map"
            ),
            ActivityEvent.Category.WORKSPACE: (
                "workspace_events"
            ),
        }

        field = (
            category_mapping.get(
                event.category
            )
        )

        if field:
            contribution[
                field
            ] += 1

        if (
            event.event_type
            == ActivityEvent
            .EventType
            .TASK_COMPLETED
        ):
            contribution[
                "tasks_completed"
            ] += 1

        current_last = (
            contribution[
                "last_contributed_at"
            ]
        )

        if (
            current_last is None
            or event.occurred_at
            > current_last
        ):
            contribution[
                "last_contributed_at"
            ] = event.occurred_at

    result = []

    for contribution in (
        workspace_data.values()
    ):
        last_at = (
            contribution[
                "last_contributed_at"
            ]
        )

        contribution[
            "last_contributed_at"
        ] = (
            last_at.isoformat()
            if last_at
            else None
        )

        result.append(
            contribution
        )

    result.sort(
        key=lambda item: (
            -item[
                "total_events"
            ],
            item[
                "workspace"
            ][
                "name"
            ].lower(),
        )
    )

    return result


def build_portfolio_summary(
    *,
    user,
):
    profile = (
        DeveloperProfile.objects
        .filter(
            user=user,
        )
        .first()
    )

    projects = (
        ExploreProject.objects
        .filter(
            owner=user,
            is_published=True,
        )
        .order_by(
            "-published_at",
            "-created_at",
        )
    )

    project_data = []

    for project in projects:
        project_data.append(
            {
                "id": str(
                    project.id
                ),
                "title": (
                    project.title
                ),
                "summary": (
                    project.summary
                ),
                "status": (
                    project.status
                ),
                "tech_stack": (
                    project.tech_stack
                ),
                "tags": (
                    project.tags
                ),
                "recruitment_status": (
                    project
                    .recruitment_status
                ),
                "repository_url": (
                    project
                    .repository_url
                ),
                "website_url": (
                    project
                    .website_url
                ),
                "cover_image_url": (
                    project
                    .cover_image_url
                ),
                "published_at": (
                    project
                    .published_at
                    .isoformat()
                    if project
                    .published_at
                    else None
                ),
            }
        )

    return {
        "profile": (
            {
                "headline": (
                    profile.headline
                ),
                "bio": (
                    profile.bio
                ),
                "skills": (
                    profile.skills
                ),
                "availability": (
                    profile.availability
                ),
                "portfolio_url": (
                    profile.portfolio_url
                ),
                "github_url": (
                    profile.github_url
                ),
            }
            if profile
            else None
        ),
        "projects": (
            project_data
        ),
        "project_count": (
            len(
                project_data
            )
        ),
    }


def build_career_signals(
    *,
    user,
    summary,
    skills,
    contributions,
    portfolio,
):
    signals = []

    if len(
        skills
    ) >= 3:
        signals.append(
            {
                "type": "skills",
                "level": "positive",
                "title": (
                    "技術スタックが形成されています"
                ),
                "description": (
                    f"{len(skills)}個のSkillが"
                    "ProfileやProjectから"
                    "確認できます。"
                ),
            }
        )

    if (
        summary[
            "published_projects"
        ]
        > 0
    ):
        signals.append(
            {
                "type": "projects",
                "level": "positive",
                "title": (
                    "公開Projectがあります"
                ),
                "description": (
                    f"{summary['published_projects']}"
                    "件のProjectを"
                    "Portfolioとして利用できます。"
                ),
            }
        )

    active_contributions = [
        contribution
        for contribution in contributions
        if contribution[
            "total_events"
        ] > 0
    ]

    if len(
        active_contributions
    ) >= 2:
        signals.append(
            {
                "type": "collaboration",
                "level": "positive",
                "title": (
                    "複数Projectで活動しています"
                ),
                "description": (
                    f"{len(active_contributions)}"
                    "個のWorkspaceで"
                    "活動履歴があります。"
                ),
            }
        )

    if (
        summary[
            "active_days_30d"
        ]
        >= 5
    ):
        signals.append(
            {
                "type": "consistency",
                "level": "positive",
                "title": (
                    "継続的な開発活動があります"
                ),
                "description": (
                    "直近30日で"
                    f"{summary['active_days_30d']}"
                    "日活動しています。"
                ),
            }
        )

    if (
        summary[
            "tasks_completed_30d"
        ]
        >= 5
    ):
        signals.append(
            {
                "type": "execution",
                "level": "positive",
                "title": (
                    "Task完了実績があります"
                ),
                "description": (
                    "直近30日で"
                    f"{summary['tasks_completed_30d']}"
                    "件のTask完了Activityがあります。"
                ),
            }
        )

    if (
        portfolio[
            "project_count"
        ]
        == 0
    ):
        signals.append(
            {
                "type": "portfolio",
                "level": "suggestion",
                "title": (
                    "公開Projectを追加できます"
                ),
                "description": (
                    "Explore Projectを公開すると"
                    "Portfolioへ自動反映できます。"
                ),
            }
        )

    if not skills:
        signals.append(
            {
                "type": "skills",
                "level": "suggestion",
                "title": (
                    "Skillを登録できます"
                ),
                "description": (
                    "ProfileへSkillを登録すると"
                    "Activityから確認できます。"
                ),
            }
        )

    return signals


def build_activity_overview(
    *,
    user,
):
    summary = (
        build_activity_summary(
            user=user,
        )
    )

    skills = (
        build_skill_summary(
            user=user,
        )
    )

    contributions = (
        build_workspace_contributions(
            user=user,
        )
    )

    portfolio = (
        build_portfolio_summary(
            user=user,
        )
    )

    career_signals = (
        build_career_signals(
            user=user,
            summary=summary,
            skills=skills,
            contributions=contributions,
            portfolio=portfolio,
        )
    )

    recent_activity = (
        get_user_activity_events(
            user=user,
        )[:12]
    )

    return {
        "summary": summary,
        "skills": skills,
        "contributions": (
            contributions
        ),
        "portfolio": portfolio,
        "career_signals": (
            career_signals
        ),
        "ai_insight": {
            "status": (
                "not_enabled"
            ),
            "summary": None,
        },
        "recent_activity": (
            recent_activity
        ),
        "generated_at": (
            timezone.now()
        ),
    }