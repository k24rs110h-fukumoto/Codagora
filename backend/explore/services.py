from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import (
    IntegrityError,
    transaction,
)
from django.utils import timezone

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from .models import (
    CommunityPost,
    ExploreEvent,
    ExploreProject,
)


def normalize_string_list(
    value,
    *,
    maximum_items=20,
    maximum_length=50,
):
    if value is None:
        return []

    if not isinstance(
        value,
        (list, tuple),
    ):
        raise ValidationError(
            "リスト形式で指定してください。"
        )

    normalized = []
    seen = set()

    for item in value:
        item = str(
            item
        ).strip()

        if not item:
            continue

        if len(item) > maximum_length:
            raise ValidationError(
                f"各項目は{maximum_length}文字以内"
                "で指定してください。"
            )

        key = item.lower()

        if key in seen:
            continue

        seen.add(key)
        normalized.append(item)

    if len(normalized) > maximum_items:
        raise ValidationError(
            f"最大{maximum_items}件までです。"
        )

    return normalized


def get_workspace_role(
    *,
    workspace,
    user,
):
    if workspace.owner_id == user.id:
        return WorkspaceMember.Role.OWNER

    membership = (
        WorkspaceMember.objects
        .filter(
            workspace=workspace,
            user=user,
            is_active=True,
        )
        .first()
    )

    if membership is None:
        return None

    return membership.role


def require_workspace_manager(
    *,
    workspace,
    user,
):
    role = get_workspace_role(
        workspace=workspace,
        user=user,
    )

    if role not in (
        WorkspaceMember.Role.OWNER,
        WorkspaceMember.Role.ADMIN,
    ):
        raise PermissionDenied(
            "WorkspaceをProjectとして"
            "公開できるのはOwnerまたは"
            "Adminのみです。"
        )

    return role


def resolve_workspace(
    *,
    workspace_id,
    actor,
):
    if workspace_id is None:
        return None

    workspace = (
        Workspace.objects
        .filter(
            id=workspace_id,
        )
        .first()
    )

    if workspace is None:
        raise ValidationError(
            "Workspaceが存在しません。"
        )

    require_workspace_manager(
        workspace=workspace,
        user=actor,
    )

    return workspace


@transaction.atomic
def create_explore_project(
    *,
    actor,
    data,
):
    workspace_id = data.pop(
        "workspace_id",
        None,
    )

    workspace = resolve_workspace(
        workspace_id=workspace_id,
        actor=actor,
    )

    title = data.get(
        "title",
        "",
    ).strip()

    summary = data.get(
        "summary",
        "",
    ).strip()

    if not title:
        raise ValidationError(
            "Project名を入力してください。"
        )

    if not summary:
        raise ValidationError(
            "Project概要を入力してください。"
        )

    is_published = bool(
        data.get(
            "is_published",
            False,
        )
    )

    try:
        return ExploreProject.objects.create(
            owner=actor,
            workspace=workspace,
            title=title,
            summary=summary,
            description=(
                data.get(
                    "description",
                    "",
                ).strip()
            ),
            status=data.get(
                "status",
                ExploreProject.Status.BUILDING,
            ),
            recruitment_status=data.get(
                "recruitment_status",
                ExploreProject
                .RecruitmentStatus
                .CLOSED,
            ),
            tags=normalize_string_list(
                data.get(
                    "tags",
                    [],
                )
            ),
            tech_stack=normalize_string_list(
                data.get(
                    "tech_stack",
                    [],
                )
            ),
            wanted_roles=normalize_string_list(
                data.get(
                    "wanted_roles",
                    [],
                )
            ),
            repository_url=data.get(
                "repository_url",
                "",
            ),
            website_url=data.get(
                "website_url",
                "",
            ),
            cover_image_url=data.get(
                "cover_image_url",
                "",
            ),
            is_published=is_published,
            published_at=(
                timezone.now()
                if is_published
                else None
            ),
        )

    except IntegrityError as error:
        raise ValidationError(
            "このWorkspaceはすでに"
            "別のProjectへ紐付いています。"
        ) from error


@transaction.atomic
def update_explore_project(
    *,
    project,
    actor,
    data,
):
    project = (
        ExploreProject.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=project.id,
        )
    )

    if project.owner_id != actor.id:
        raise PermissionDenied(
            "このProjectを編集する"
            "権限がありません。"
        )

    if "workspace_id" in data:
        project.workspace = resolve_workspace(
            workspace_id=data.pop(
                "workspace_id"
            ),
            actor=actor,
        )

    for field in (
        "title",
        "summary",
        "description",
    ):
        if field in data:
            setattr(
                project,
                field,
                data[field].strip(),
            )

    for field in (
        "repository_url",
        "website_url",
        "cover_image_url",
    ):
        if field in data:
            setattr(
                project,
                field,
                data[field],
            )

    if not project.title:
        raise ValidationError(
            "Project名を入力してください。"
        )

    if not project.summary:
        raise ValidationError(
            "Project概要を入力してください。"
        )

    if "status" in data:
        project.status = data[
            "status"
        ]

    if "recruitment_status" in data:
        project.recruitment_status = (
            data[
                "recruitment_status"
            ]
        )

    for field in (
        "tags",
        "tech_stack",
        "wanted_roles",
    ):
        if field in data:
            setattr(
                project,
                field,
                normalize_string_list(
                    data[field]
                ),
            )

    if "is_published" in data:
        publish = bool(
            data["is_published"]
        )

        if (
            publish
            and not project.is_published
        ):
            project.published_at = (
                timezone.now()
            )

        if not publish:
            project.published_at = None

        project.is_published = publish

    try:
        project.save()

    except IntegrityError as error:
        raise ValidationError(
            "このWorkspaceはすでに"
            "別のProjectへ紐付いています。"
        ) from error

    return project


@transaction.atomic
def delete_explore_project(
    *,
    project,
    actor,
):
    project = (
        ExploreProject.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=project.id,
        )
    )

    if project.owner_id != actor.id:
        raise PermissionDenied(
            "このProjectを削除する"
            "権限がありません。"
        )

    project.delete()


@transaction.atomic
def create_community_post(
    *,
    actor,
    data,
):
    project = None

    project_id = data.get(
        "project_id"
    )

    if project_id:
        project = (
            ExploreProject.objects
            .filter(
                id=project_id,
                is_published=True,
            )
            .first()
        )

        if project is None:
            raise ValidationError(
                "公開Projectが存在しません。"
            )

    title = data.get(
        "title",
        "",
    ).strip()

    body = data.get(
        "body",
        "",
    ).strip()

    if not title:
        raise ValidationError(
            "タイトルを入力してください。"
        )

    if not body:
        raise ValidationError(
            "本文を入力してください。"
        )

    return CommunityPost.objects.create(
        author=actor,
        project=project,
        kind=data.get(
            "kind",
            CommunityPost.Kind.DISCUSSION,
        ),
        title=title,
        body=body,
        tags=normalize_string_list(
            data.get(
                "tags",
                [],
            )
        ),
        is_published=True,
    )


@transaction.atomic
def update_community_post(
    *,
    post,
    actor,
    data,
):
    post = (
        CommunityPost.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=post.id,
            deleted_at__isnull=True,
        )
    )

    if post.author_id != actor.id:
        raise PermissionDenied(
            "自分の投稿のみ編集できます。"
        )

    if "title" in data:
        title = data[
            "title"
        ].strip()

        if not title:
            raise ValidationError(
                "タイトルを入力してください。"
            )

        post.title = title

    if "body" in data:
        body = data[
            "body"
        ].strip()

        if not body:
            raise ValidationError(
                "本文を入力してください。"
            )

        post.body = body

    if "kind" in data:
        post.kind = data[
            "kind"
        ]

    if "tags" in data:
        post.tags = normalize_string_list(
            data["tags"]
        )

    post.save()

    return post


@transaction.atomic
def delete_community_post(
    *,
    post,
    actor,
):
    post = (
        CommunityPost.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=post.id,
            deleted_at__isnull=True,
        )
    )

    if post.author_id != actor.id:
        raise PermissionDenied(
            "自分の投稿のみ削除できます。"
        )

    post.is_published = False
    post.deleted_at = timezone.now()

    post.save(
        update_fields=(
            "is_published",
            "deleted_at",
            "updated_at",
        )
    )

    return post


@transaction.atomic
def create_explore_event(
    *,
    actor,
    data,
):
    starts_at = data.get(
        "starts_at"
    )

    ends_at = data.get(
        "ends_at"
    )

    if starts_at is None:
        raise ValidationError(
            "開始日時を指定してください。"
        )

    if ends_at is None:
        raise ValidationError(
            "終了日時を指定してください。"
        )

    if ends_at <= starts_at:
        raise ValidationError(
            "終了日時は開始日時より"
            "後にしてください。"
        )

    title = data.get(
        "title",
        "",
    ).strip()

    summary = data.get(
        "summary",
        "",
    ).strip()

    if not title:
        raise ValidationError(
            "Event名を入力してください。"
        )

    if not summary:
        raise ValidationError(
            "Event概要を入力してください。"
        )

    publish = bool(
        data.get(
            "is_published",
            False,
        )
    )

    return ExploreEvent.objects.create(
        organizer=actor,
        title=title,
        summary=summary,
        description=(
            data.get(
                "description",
                "",
            ).strip()
        ),
        starts_at=starts_at,
        ends_at=ends_at,
        location_name=(
            data.get(
                "location_name",
                "",
            ).strip()
        ),
        online_url=data.get(
            "online_url",
            "",
        ),
        tags=normalize_string_list(
            data.get(
                "tags",
                [],
            )
        ),
        capacity=data.get(
            "capacity"
        ),
        is_published=publish,
        published_at=(
            timezone.now()
            if publish
            else None
        ),
    )


@transaction.atomic
def update_explore_event(
    *,
    event,
    actor,
    data,
):
    event = (
        ExploreEvent.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=event.id,
            deleted_at__isnull=True,
        )
    )

    if event.organizer_id != actor.id:
        raise PermissionDenied(
            "このEventを編集する"
            "権限がありません。"
        )

    for field in (
        "title",
        "summary",
        "description",
        "location_name",
    ):
        if field in data:
            setattr(
                event,
                field,
                data[field].strip(),
            )

    for field in (
        "online_url",
        "capacity",
    ):
        if field in data:
            setattr(
                event,
                field,
                data[field],
            )

    if "starts_at" in data:
        event.starts_at = (
            data["starts_at"]
        )

    if "ends_at" in data:
        event.ends_at = (
            data["ends_at"]
        )

    if event.ends_at <= event.starts_at:
        raise ValidationError(
            "終了日時は開始日時より"
            "後にしてください。"
        )

    if not event.title:
        raise ValidationError(
            "Event名を入力してください。"
        )

    if not event.summary:
        raise ValidationError(
            "Event概要を入力してください。"
        )

    if "tags" in data:
        event.tags = normalize_string_list(
            data["tags"]
        )

    if "is_published" in data:
        publish = bool(
            data["is_published"]
        )

        if (
            publish
            and not event.is_published
        ):
            event.published_at = (
                timezone.now()
            )

        if not publish:
            event.published_at = None

        event.is_published = publish

    event.save()

    return event


@transaction.atomic
def delete_explore_event(
    *,
    event,
    actor,
):
    event = (
        ExploreEvent.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=event.id,
            deleted_at__isnull=True,
        )
    )

    if event.organizer_id != actor.id:
        raise PermissionDenied(
            "このEventを削除する"
            "権限がありません。"
        )

    event.is_published = False
    event.deleted_at = (
        timezone.now()
    )

    event.save(
        update_fields=(
            "is_published",
            "deleted_at",
            "updated_at",
        )
    )

    return event