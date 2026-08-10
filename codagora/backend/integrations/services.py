import base64
import hashlib
import hmac
import secrets

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import (
    IntegrityError,
    transaction,
)
from django.utils import timezone
from django.utils.dateparse import (
    parse_datetime,
)

from workspaces.models import (
    Workspace,
    WorkspaceMember,
)

from activity.recorders import (
    record_github_repository_linked,
    record_github_synced,
)

from notifications.recorders import (
    notify_github_repository_linked,
)

from .crypto import encrypt_secret
from .github_client import (
    GitHubAPIError,
    apply_token_payload,
    exchange_code_for_user_token,
    get_authenticated_github_user,
    get_installation_access_token,
    get_valid_user_access_token,
    github_request,
    list_user_installation_repositories,
    list_user_installations,
)
from .models import (
    GitHubConnection,
    GitHubOAuthState,
    WorkspaceGitHubRepository,
)


def hash_github_state(
    value,
):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _base64url_without_padding(
    value,
):
    return (
        base64.urlsafe_b64encode(
            value
        )
        .rstrip(b"=")
        .decode("ascii")
    )


def build_github_pkce_verifier(
    state,
):
    key = settings.SECRET_KEY.encode(
        "utf-8"
    )

    message = (
        "codagora-github-pkce:"
        f"{state.state_hash}"
    ).encode(
        "utf-8"
    )

    digest = hmac.new(
        key,
        message,
        hashlib.sha256,
    ).digest()

    return (
        _base64url_without_padding(
            digest
        )
    )


def build_github_pkce_challenge(
    state,
):
    verifier = (
        build_github_pkce_verifier(
            state
        )
    )

    digest = hashlib.sha256(
        verifier.encode(
            "ascii"
        )
    ).digest()

    return (
        _base64url_without_padding(
            digest
        )
    )


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

    if not membership:
        return None

    return membership.role


def require_github_viewer(
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
        WorkspaceMember.Role.MEMBER,
    ):
        raise PermissionDenied(
            "GitHub連携を閲覧するには"
            "Member以上の権限が"
            "必要です。"
        )

    return role


def require_github_manager(
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
            "GitHub連携を管理できるのは"
            "OwnerまたはAdminのみです。"
        )

    return role


@transaction.atomic
def create_github_oauth_state(
    *,
    workspace,
    user,
    lifetime_minutes=10,
):
    workspace = (
        Workspace.objects
        .select_for_update(
            of=("self",)
        )
        .get(
            id=workspace.id,
        )
    )

    require_github_manager(
        workspace=workspace,
        user=user,
    )

    raw_state = (
        secrets.token_urlsafe(
            32
        )
    )

    state = (
        GitHubOAuthState.objects
        .create(
            user=user,
            workspace=workspace,
            state_hash=(
                hash_github_state(
                    raw_state
                )
            ),
            expires_at=(
                timezone.now()
                + timedelta(
                    minutes=(
                        lifetime_minutes
                    )
                )
            ),
        )
    )

    return (
        state,
        raw_state,
    )


@transaction.atomic
def consume_github_oauth_state(
    raw_state,
):
    state = (
        GitHubOAuthState.objects
        .select_related(
            "user",
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .filter(
            state_hash=(
                hash_github_state(
                    raw_state
                )
            )
        )
        .first()
    )

    if not state:
        raise ValidationError(
            "GitHub接続stateが"
            "無効です。"
        )

    if state.used_at:
        raise ValidationError(
            "このGitHub接続stateは"
            "すでに使用されています。"
        )

    if (
        state.expires_at
        <= timezone.now()
    ):
        raise ValidationError(
            "GitHub接続stateの"
            "有効期限が切れています。"
        )

    state.used_at = timezone.now()

    state.save(
        update_fields=(
            "used_at",
        )
    )

    return state


def verify_installation_for_user(
    *,
    access_token,
    installation_id,
):
    installations = (
        list_user_installations(
            access_token
        )
    )

    installation_id = int(
        installation_id
    )

    for installation in installations:
        if (
            int(
                installation["id"]
            )
            == installation_id
        ):
            return installation

    raise ValidationError(
        "このGitHub Installationへ"
        "アクセスする権限がありません。"
    )


@transaction.atomic
def save_github_connection(
    *,
    user,
    github_user,
    token_payload,
):
    github_user_id = int(
        github_user["id"]
    )

    conflicting = (
        GitHubConnection.objects
        .filter(
            github_user_id=(
                github_user_id
            )
        )
        .exclude(
            user=user,
        )
        .exists()
    )

    if conflicting:
        raise ValidationError(
            "このGitHubアカウントは"
            "別のCodagoraアカウントに"
            "接続されています。"
        )

    connection = (
        GitHubConnection.objects
        .filter(
            user=user,
        )
        .first()
    )

    if connection is None:
        connection = GitHubConnection(
            user=user,
            github_user_id=(
                github_user_id
            ),
            login=(
                github_user["login"]
            ),
            access_token_encrypted="",
        )

    connection.github_user_id = (
        github_user_id
    )

    connection.login = (
        github_user["login"]
    )

    connection.avatar_url = (
        github_user.get(
            "avatar_url",
            "",
        )
    )

    apply_token_payload(
        connection=connection,
        payload=token_payload,
    )

    connection.last_verified_at = (
        timezone.now()
    )

    connection.save()

    return connection


def complete_github_connection(
    *,
    state,
    code,
    installation_id=None,
):
    code_verifier = None

    if state.installation_id:
        code_verifier = (
            build_github_pkce_verifier(
                state
            )
        )

    if code_verifier:
        token_payload = (
            exchange_code_for_user_token(
                code=code,
                code_verifier=(
                    code_verifier
                ),
            )
        )

    else:
        token_payload = (
            exchange_code_for_user_token(
                code=code,
            )
        )

    access_token = (
        token_payload[
            "access_token"
        ]
    )

    github_user = (
        get_authenticated_github_user(
            access_token
        )
    )

    target_installation_id = (
        installation_id
        or state.installation_id
    )

    if target_installation_id:
        verify_installation_for_user(
            access_token=access_token,
            installation_id=(
                target_installation_id
            ),
        )

    connection = save_github_connection(
        user=state.user,
        github_user=github_user,
        token_payload=token_payload,
    )

    return connection


def get_connection_or_error(
    user,
):
    connection = (
        GitHubConnection.objects
        .filter(
            user=user,
        )
        .first()
    )

    if not connection:
        raise ValidationError(
            "GitHubアカウントが"
            "接続されていません。"
        )

    return connection


def get_user_github_installations(
    *,
    user,
):
    connection = (
        get_connection_or_error(
            user
        )
    )

    access_token = (
        get_valid_user_access_token(
            connection
        )
    )

    return (
        list_user_installations(
            access_token
        )
    )


def get_user_installation_repositories(
    *,
    user,
    installation_id,
):
    connection = (
        get_connection_or_error(
            user
        )
    )

    access_token = (
        get_valid_user_access_token(
            connection
        )
    )

    verify_installation_for_user(
        access_token=access_token,
        installation_id=(
            installation_id
        ),
    )

    return (
        list_user_installation_repositories(
            access_token=access_token,
            installation_id=(
                installation_id
            ),
        )
    )


def find_user_installation_repository(
    *,
    user,
    installation_id,
    repository_id,
):
    repositories = (
        get_user_installation_repositories(
            user=user,
            installation_id=(
                installation_id
            ),
        )
    )

    repository_id = int(
        repository_id
    )

    for repository in repositories:
        if (
            int(repository["id"])
            == repository_id
        ):
            return repository

    raise ValidationError(
        "指定したRepositoryへ"
        "アクセスできません。"
    )


def apply_repository_payload(
    *,
    linked_repository,
    repository,
):
    linked_repository.github_repository_id = (
        int(repository["id"])
    )

    linked_repository.owner_login = (
        repository[
            "owner"
        ][
            "login"
        ]
    )

    linked_repository.name = (
        repository[
            "name"
        ]
    )

    linked_repository.full_name = (
        repository[
            "full_name"
        ]
    )

    linked_repository.description = (
        repository.get(
            "description"
        )
        or ""
    )

    linked_repository.html_url = (
        repository[
            "html_url"
        ]
    )

    linked_repository.default_branch = (
        repository.get(
            "default_branch"
        )
        or ""
    )

    linked_repository.is_private = (
        bool(
            repository.get(
                "private",
                False,
            )
        )
    )

    linked_repository.is_archived = (
        bool(
            repository.get(
                "archived",
                False,
            )
        )
    )

    linked_repository.stargazers_count = (
        int(
            repository.get(
                "stargazers_count",
                0,
            )
            or 0
        )
    )

    linked_repository.forks_count = (
        int(
            repository.get(
                "forks_count",
                0,
            )
            or 0
        )
    )

    linked_repository.open_issues_count = (
        int(
            repository.get(
                "open_issues_count",
                0,
            )
            or 0
        )
    )

    pushed_at = repository.get(
        "pushed_at"
    )

    linked_repository.pushed_at = (
        parse_datetime(
            pushed_at
        )
        if pushed_at
        else None
    )


def normalize_installation(
    installation,
):
    account = (
        installation.get(
            "account"
        )
        or {}
    )

    return {
        "id": installation["id"],
        "account_login": (
            account.get(
                "login",
                "",
            )
        ),
        "account_type": (
            account.get(
                "type",
                "",
            )
        ),
        "avatar_url": (
            account.get(
                "avatar_url",
                "",
            )
        ),
        "repository_selection": (
            installation.get(
                "repository_selection",
                "",
            )
        ),
        "permissions": (
            installation.get(
                "permissions",
                {},
            )
        ),
    }


def normalize_remote_repository(
    repository,
):
    return {
        "id": repository["id"],
        "name": repository["name"],
        "full_name": (
            repository["full_name"]
        ),
        "private": bool(
            repository.get(
                "private",
                False,
            )
        ),
        "html_url": (
            repository["html_url"]
        ),
        "description": (
            repository.get(
                "description"
            )
            or ""
        ),
        "default_branch": (
            repository.get(
                "default_branch"
            )
            or ""
        ),
        "archived": bool(
            repository.get(
                "archived",
                False,
            )
        ),
        "permissions": (
            repository.get(
                "permissions",
                {}
            )
        ),
    }


def link_workspace_repository(
    *,
    workspace,
    actor,
    installation_id,
    repository_id,
    is_primary=False,
):
    require_github_manager(
        workspace=workspace,
        user=actor,
    )

    repository = (
        find_user_installation_repository(
            user=actor,
            installation_id=(
                installation_id
            ),
            repository_id=(
                repository_id
            ),
        )
    )

    with transaction.atomic():
        locked_workspace = (
            Workspace.objects
            .select_for_update(
                of=("self",)
            )
            .get(
                id=workspace.id,
            )
        )

        require_github_manager(
            workspace=locked_workspace,
            user=actor,
        )

        existing = (
            WorkspaceGitHubRepository.objects
            .filter(
                workspace=locked_workspace,
                github_repository_id=(
                    repository_id
                ),
                unlinked_at__isnull=True,
            )
            .first()
        )

        if existing:
            raise ValidationError(
                "このRepositoryは"
                "すでに連携されています。"
            )

        active_count = (
            WorkspaceGitHubRepository.objects
            .filter(
                workspace=locked_workspace,
                unlinked_at__isnull=True,
            )
            .count()
        )

        make_primary = (
            is_primary
            or active_count == 0
        )

        if make_primary:
            (
                WorkspaceGitHubRepository
                .objects
                .filter(
                    workspace=(
                        locked_workspace
                    ),
                    is_primary=True,
                    unlinked_at__isnull=True,
                )
                .update(
                    is_primary=False,
                )
            )

        linked = (
            WorkspaceGitHubRepository(
                workspace=(
                    locked_workspace
                ),
                installation_id=(
                    installation_id
                ),
                github_repository_id=(
                    repository_id
                ),
                linked_by=actor,
                is_primary=(
                    make_primary
                ),
            )
        )

        apply_repository_payload(
            linked_repository=linked,
            repository=repository,
        )

        linked.last_synced_at = (
            timezone.now()
        )

        try:
            linked.save()

        except IntegrityError as error:
            raise ValidationError(
                "Repositoryを"
                "連携できませんでした。"
            ) from error

        record_github_repository_linked(
            workspace=locked_workspace,
            actor=actor,
            linked_repository=linked,
        )

        notify_github_repository_linked(
            workspace=locked_workspace,
            actor=actor,
            linked_repository=linked,
        )

    return linked


@transaction.atomic
def set_primary_repository(
    *,
    linked_repository,
    actor,
):
    linked_repository = (
        WorkspaceGitHubRepository.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=linked_repository.id,
            unlinked_at__isnull=True,
        )
    )

    require_github_manager(
        workspace=(
            linked_repository.workspace
        ),
        user=actor,
    )

    (
        WorkspaceGitHubRepository.objects
        .filter(
            workspace=(
                linked_repository.workspace
            ),
            is_primary=True,
            unlinked_at__isnull=True,
        )
        .exclude(
            id=linked_repository.id
        )
        .update(
            is_primary=False,
        )
    )

    linked_repository.is_primary = True

    linked_repository.save(
        update_fields=(
            "is_primary",
            "updated_at",
        )
    )

    return linked_repository


@transaction.atomic
def unlink_workspace_repository(
    *,
    linked_repository,
    actor,
):
    linked_repository = (
        WorkspaceGitHubRepository.objects
        .select_related(
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .get(
            id=linked_repository.id,
            unlinked_at__isnull=True,
        )
    )

    workspace = (
        linked_repository.workspace
    )

    require_github_manager(
        workspace=workspace,
        user=actor,
    )

    was_primary = (
        linked_repository.is_primary
    )

    linked_repository.is_primary = False
    linked_repository.unlinked_at = (
        timezone.now()
    )
    linked_repository.unlinked_by = (
        actor
    )

    linked_repository.save(
        update_fields=(
            "is_primary",
            "unlinked_at",
            "unlinked_by",
            "updated_at",
        )
    )

    if was_primary:
        replacement = (
            WorkspaceGitHubRepository.objects
            .filter(
                workspace=workspace,
                unlinked_at__isnull=True,
            )
            .order_by(
                "created_at",
            )
            .first()
        )

        if replacement:
            replacement.is_primary = True

            replacement.save(
                update_fields=(
                    "is_primary",
                    "updated_at",
                )
            )

    return linked_repository


def sync_workspace_repository(
    *,
    linked_repository,
    actor,
):
    require_github_manager(
        workspace=(
            linked_repository.workspace
        ),
        user=actor,
    )

    token = (
        get_installation_access_token(
            installation_id=(
                linked_repository
                .installation_id
            ),
            repository_id=(
                linked_repository
                .github_repository_id
            ),
        )
    )

    repository = github_request(
        "GET",
        (
            "/repos/"
            f"{linked_repository.full_name}"
        ),
        token=token,
    )

    with transaction.atomic():
        locked = (
            WorkspaceGitHubRepository.objects
            .select_for_update(
                of=("self",)
            )
            .get(
                id=linked_repository.id,
                unlinked_at__isnull=True,
            )
        )

        apply_repository_payload(
            linked_repository=locked,
            repository=repository,
        )

        locked.last_synced_at = (
            timezone.now()
        )

        locked.save()

        record_github_synced(
            workspace=locked.workspace,
            actor=actor,
            linked_repository=locked,
        )

    return locked


def get_repository_overview(
    *,
    linked_repository,
    user,
):
    require_github_viewer(
        workspace=(
            linked_repository.workspace
        ),
        user=user,
    )

    token = (
        get_installation_access_token(
            installation_id=(
                linked_repository
                .installation_id
            ),
            repository_id=(
                linked_repository
                .github_repository_id
            ),
        )
    )

    repository = github_request(
        "GET",
        (
            "/repos/"
            f"{linked_repository.full_name}"
        ),
        token=token,
    )

    try:
        commits = github_request(
            "GET",
            (
                "/repos/"
                f"{linked_repository.full_name}"
                "/commits"
            ),
            token=token,
            params={
                "per_page": 10,
            },
        )

    except GitHubAPIError as error:
        if error.status_code == 409:
            commits = []
        else:
            raise


    try:
        pull_requests = github_request(
            "GET",
            (
                "/repos/"
                f"{linked_repository.full_name}"
                "/pulls"
            ),
            token=token,
            params={
                "state": "open",
                "per_page": 10,
            },
        )

    except GitHubAPIError as error:
        if error.status_code == 409:
            pull_requests = []
        else:
            raise

    recent_commits = []

    for commit in commits:
        commit_data = (
            commit.get(
                "commit"
            )
            or {}
        )

        author_data = (
            commit_data.get(
                "author"
            )
            or {}
        )

        github_author = (
            commit.get(
                "author"
            )
            or {}
        )

        recent_commits.append(
            {
                "sha": (
                    commit.get(
                        "sha",
                        "",
                    )
                ),
                "message": (
                    commit_data.get(
                        "message",
                        "",
                    )
                ),
                "html_url": (
                    commit.get(
                        "html_url",
                        "",
                    )
                ),
                "author_name": (
                    author_data.get(
                        "name",
                        "",
                    )
                ),
                "author_login": (
                    github_author.get(
                        "login",
                        "",
                    )
                ),
                "author_avatar_url": (
                    github_author.get(
                        "avatar_url",
                        "",
                    )
                ),
                "committed_at": (
                    author_data.get(
                        "date"
                    )
                ),
            }
        )

    open_pull_requests = []

    for pull_request in pull_requests:
        author = (
            pull_request.get(
                "user"
            )
            or {}
        )

        open_pull_requests.append(
            {
                "number": (
                    pull_request[
                        "number"
                    ]
                ),
                "title": (
                    pull_request[
                        "title"
                    ]
                ),
                "html_url": (
                    pull_request[
                        "html_url"
                    ]
                ),
                "draft": bool(
                    pull_request.get(
                        "draft",
                        False,
                    )
                ),
                "author_login": (
                    author.get(
                        "login",
                        "",
                    )
                ),
                "author_avatar_url": (
                    author.get(
                        "avatar_url",
                        "",
                    )
                ),
                "created_at": (
                    pull_request.get(
                        "created_at"
                    )
                ),
                "updated_at": (
                    pull_request.get(
                        "updated_at"
                    )
                ),
            }
        )

    return {
        "repository": {
            "id": repository["id"],
            "name": repository["name"],
            "full_name": (
                repository[
                    "full_name"
                ]
            ),
            "description": (
                repository.get(
                    "description"
                )
                or ""
            ),
            "html_url": (
                repository[
                    "html_url"
                ]
            ),
            "private": bool(
                repository.get(
                    "private",
                    False,
                )
            ),
            "archived": bool(
                repository.get(
                    "archived",
                    False,
                )
            ),
            "default_branch": (
                repository.get(
                    "default_branch"
                )
            ),
            "stargazers_count": (
                repository.get(
                    "stargazers_count",
                    0,
                )
            ),
            "forks_count": (
                repository.get(
                    "forks_count",
                    0,
                )
            ),
            "open_issues_count": (
                repository.get(
                    "open_issues_count",
                    0,
                )
            ),
            "pushed_at": (
                repository.get(
                    "pushed_at"
                )
            ),
        },
        "recent_commits": (
            recent_commits
        ),
        "open_pull_requests": (
            open_pull_requests
        ),
    }

@transaction.atomic
def attach_installation_to_github_state(
    *,
    raw_state,
    installation_id,
):
    state = (
        GitHubOAuthState.objects
        .select_related(
            "user",
            "workspace",
        )
        .select_for_update(
            of=("self",)
        )
        .filter(
            state_hash=hash_github_state(
                raw_state
            )
        )
        .first()
    )

    if not state:
        raise ValidationError(
            "GitHub接続stateが無効です。"
        )

    if state.used_at:
        raise ValidationError(
            "このGitHub接続stateは"
            "すでに使用されています。"
        )

    if state.expires_at <= timezone.now():
        raise ValidationError(
            "GitHub接続stateの"
            "有効期限が切れています。"
        )

    installation_id = int(
        installation_id
    )

    if (
        state.installation_id
        and state.installation_id
        != installation_id
    ):
        raise ValidationError(
            "GitHub Installationが"
            "一致しません。"
        )

    state.installation_id = installation_id

    state.save(
        update_fields=(
            "installation_id",
        )
    )

    return state
