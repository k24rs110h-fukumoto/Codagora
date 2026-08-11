from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from django.conf import settings
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.http import (
    HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from workspaces.selectors import (
    get_accessible_workspaces,
)

from .github_client import (
    GitHubAPIError,
)
from .models import (
    WorkspaceGitHubRepository,
)
from .selectors import (
    get_github_connection,
    get_workspace_github_repositories,
)
from .serializers import (
    GitHubConnectionSerializer,
    GitHubInstallationSerializer,
    GitHubRemoteRepositorySerializer,
    GitHubRepositoryLinkSerializer,
    WorkspaceGitHubRepositorySerializer,
)
from .services import (
    attach_installation_to_github_state,
    build_github_pkce_challenge,
    complete_github_connection,
    consume_github_oauth_state,
    create_github_oauth_state,
    get_repository_overview,
    get_user_github_installations,
    get_user_installation_repositories,
    link_workspace_repository,
    normalize_installation,
    normalize_remote_repository,
    require_github_manager,
    require_github_viewer,
    set_primary_repository,
    sync_workspace_repository,
    unlink_workspace_repository,
)


class GitHubUpstreamError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = (
        "GitHub APIとの通信に失敗しました。"
    )


class GitHubMobileRedirectResponse(
    HttpResponseRedirect
):
    allowed_schemes = [
        "https",
        "codagora",
    ]


def apply_sensitive_response_headers(
    response,
):
    response["Cache-Control"] = (
        "no-store, max-age=0"
    )

    response["Pragma"] = "no-cache"

    response["Referrer-Policy"] = (
        "no-referrer"
    )

    response["X-Content-Type-Options"] = (
        "nosniff"
    )

    return response


def handle_service_error(
    error,
):
    if isinstance(
        error,
        DjangoPermissionDenied,
    ):
        raise PermissionDenied(
            detail=str(error),
        ) from error

    if isinstance(
        error,
        DjangoValidationError,
    ):
        if hasattr(
            error,
            "message_dict",
        ):
            raise ValidationError(
                error.message_dict
            ) from error

        raise ValidationError(
            {
                "detail": error.messages,
            }
        ) from error

    if isinstance(
        error,
        GitHubAPIError,
    ):
        raise GitHubUpstreamError(
            detail=(
                "GitHub APIとの通信に"
                "失敗しました。"
            )
        ) from error

    raise error


def get_github_oauth_configuration():
    client_id = str(
        getattr(
            settings,
            "GITHUB_APP_CLIENT_ID",
            "",
        )
        or ""
    ).strip()

    callback_url = str(
        getattr(
            settings,
            "GITHUB_APP_CALLBACK_URL",
            "",
        )
        or ""
    ).strip()

    if not client_id:
        raise DjangoValidationError(
            "GitHub App Client IDが"
            "設定されていません。"
        )

    if not callback_url:
        raise DjangoValidationError(
            "GitHub App Callback URLが"
            "設定されていません。"
        )

    parsed = urlsplit(
        callback_url
    )

    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise DjangoValidationError(
            "GitHub App Callback URLが"
            "不正です。"
        )

    if (
        parsed.scheme == "https"
        and parsed.hostname
    ):
        return (
            client_id,
            callback_url,
        )

    loopback_hosts = {
        "127.0.0.1",
        "localhost",
        "::1",
    }

    if (
        settings.DEBUG
        and parsed.scheme == "http"
        and parsed.hostname
        in loopback_hosts
    ):
        return (
            client_id,
            callback_url,
        )

    raise DjangoValidationError(
        "GitHub App Callback URLは"
        "本番環境ではHTTPSが必要です。"
    )


def build_mobile_redirect(
    *,
    success,
    workspace_slug=None,
    error_code=None,
):
    base_url = str(
        getattr(
            settings,
            "GITHUB_APP_MOBILE_REDIRECT_URL",
            "",
        )
        or ""
    ).strip()

    if not base_url:
        return None

    parsed = urlsplit(
        base_url
    )

    if (
        parsed.username
        or parsed.password
        or parsed.fragment
    ):
        return None

    if parsed.scheme == "https":
        if not parsed.hostname:
            return None

    elif parsed.scheme == "codagora":
        if not parsed.netloc:
            return None

    else:
        return None

    reserved_keys = {
        "status",
        "workspace",
        "error",
    }

    query_items = [
        (
            key,
            value,
        )
        for key, value
        in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if key not in reserved_keys
    ]

    query_items.append(
        (
            "status",
            (
                "success"
                if success
                else "error"
            ),
        )
    )

    if workspace_slug:
        query_items.append(
            (
                "workspace",
                workspace_slug,
            )
        )

    if error_code:
        query_items.append(
            (
                "error",
                error_code,
            )
        )

    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urlencode(
                query_items
            ),
            "",
        )
    )


def github_callback_response(
    *,
    success,
    workspace_slug=None,
    error_code=None,
    http_status=None,
):
    redirect_url = (
        build_mobile_redirect(
            success=success,
            workspace_slug=(
                workspace_slug
            ),
            error_code=(
                error_code
            ),
        )
    )

    if redirect_url:
        return apply_sensitive_response_headers(
            GitHubMobileRedirectResponse(
                redirect_url
            )
        )

    if success:
        payload = {
            "status": "success",
        }

        if workspace_slug:
            payload[
                "workspace"
            ] = workspace_slug

        response_status = (
            http_status
            or status.HTTP_200_OK
        )

    else:
        payload = {
            "status": "error",
            "code": (
                error_code
                or "github_connect_failed"
            ),
        }

        response_status = (
            http_status
            or status.HTTP_400_BAD_REQUEST
        )

    return apply_sensitive_response_headers(
        Response(
            payload,
            status=response_status,
        )
    )


class WorkspaceGitHubMixin:
    def get_workspace(self):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=self.kwargs[
                "workspace_slug"
            ],
        )

    def get_linked_repository(
        self,
    ):
        return get_object_or_404(
            WorkspaceGitHubRepository
            .objects
            .select_related(
                "workspace",
                "linked_by",
            ),
            id=self.kwargs[
                "repository_link_id"
            ],
            workspace=(
                self.get_workspace()
            ),
            unlinked_at__isnull=True,
        )


class GitHubConnectStartView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        try:
            state, raw_state = (
                create_github_oauth_state(
                    workspace=workspace,
                    user=request.user,
                    lifetime_minutes=(
                        settings
                        .GITHUB_OAUTH_STATE_MINUTES
                    ),
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        app_slug = str(
            getattr(
                settings,
                "GITHUB_APP_SLUG",
                "",
            )
            or ""
        ).strip()

        if not app_slug:
            raise ValidationError(
                {
                    "detail": (
                        "GitHub Appが"
                        "設定されていません。"
                    )
                }
            )

        url = (
            "https://github.com/apps/"
            f"{app_slug}/installations/new?"
            + urlencode(
                {
                    "state": raw_state,
                }
            )
        )

        return apply_sensitive_response_headers(
            Response(
                {
                    "authorization_url": url,
                    "expires_at": (
                        state.expires_at
                    ),
                },
                status=(
                    status.HTTP_200_OK
                ),
            )
        )


class GitHubCallbackView(APIView):
    permission_classes = (
        AllowAny,
    )

    authentication_classes = ()

    def get(
        self,
        request,
    ):
        raw_state = (
            request.query_params.get(
                "state"
            )
        )

        code = (
            request.query_params.get(
                "code"
            )
        )

        github_error = (
            request.query_params.get(
                "error"
            )
        )

        if github_error:
            if not raw_state:
                return github_callback_response(
                    success=False,
                    error_code=(
                        "invalid_callback"
                    ),
                )

            try:
                consume_github_oauth_state(
                    raw_state
                )

            except DjangoValidationError:
                return github_callback_response(
                    success=False,
                    error_code=(
                        "invalid_callback"
                    ),
                )

            error_code = (
                "authorization_denied"
                if github_error
                == "access_denied"
                else (
                    "github_authorization_failed"
                )
            )

            return github_callback_response(
                success=False,
                error_code=error_code,
            )

        if not raw_state or not code:
            return github_callback_response(
                success=False,
                error_code=(
                    "invalid_callback"
                ),
            )

        try:
            state = (
                consume_github_oauth_state(
                    raw_state
                )
            )

            # OAuth開始時にはOwner/Adminだったとしても、
            # Callback時点でも権限を再確認する。
            require_github_manager(
                workspace=state.workspace,
                user=state.user,
            )

            # installation_idはOptional。
            # stateに保存されている場合はService側で
            # GitHub APIを使って本当に本人のInstallationか検証する。
            complete_github_connection(
                state=state,
                code=code,
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
            GitHubAPIError,
        ):
            return github_callback_response(
                success=False,
                error_code=(
                    "github_connect_failed"
                ),
            )

        return github_callback_response(
            success=True,
            workspace_slug=(
                state.workspace.slug
            ),
        )


class WorkspaceGitHubOverviewView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        try:
            require_github_viewer(
                workspace=workspace,
                user=request.user,
            )

        except DjangoPermissionDenied as error:
            handle_service_error(
                error
            )

        connection = (
            get_github_connection(
                user=request.user,
            )
        )

        repositories = (
            get_workspace_github_repositories(
                workspace=workspace,
            )
        )

        return Response(
            {
                "github_connected": (
                    connection
                    is not None
                ),
                "connection": (
                    GitHubConnectionSerializer(
                        connection
                    ).data
                    if connection
                    else None
                ),
                "repositories": (
                    WorkspaceGitHubRepositorySerializer(
                        repositories,
                        many=True,
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )


class GitHubInstallationListView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        try:
            require_github_manager(
                workspace=workspace,
                user=request.user,
            )

            installations = (
                get_user_github_installations(
                    user=request.user,
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
            GitHubAPIError,
        ) as error:
            handle_service_error(
                error
            )

        normalized = [
            normalize_installation(
                installation
            )
            for installation
            in installations
        ]

        return Response(
            GitHubInstallationSerializer(
                normalized,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class GitHubInstallationRepositoryListView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        installation_id,
    ):
        workspace = (
            self.get_workspace()
        )

        try:
            require_github_manager(
                workspace=workspace,
                user=request.user,
            )

            repositories = (
                get_user_installation_repositories(
                    user=request.user,
                    installation_id=(
                        installation_id
                    ),
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
            GitHubAPIError,
        ) as error:
            handle_service_error(
                error
            )

        normalized = [
            normalize_remote_repository(
                repository
            )
            for repository
            in repositories
        ]

        return Response(
            GitHubRemoteRepositorySerializer(
                normalized,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceGitHubRepositoryListLinkView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        try:
            require_github_viewer(
                workspace=workspace,
                user=request.user,
            )

        except DjangoPermissionDenied as error:
            handle_service_error(
                error
            )

        repositories = (
            get_workspace_github_repositories(
                workspace=workspace,
            )
        )

        return Response(
            WorkspaceGitHubRepositorySerializer(
                repositories,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request,
        workspace_slug,
    ):
        serializer = (
            GitHubRepositoryLinkSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            linked = (
                link_workspace_repository(
                    workspace=(
                        self.get_workspace()
                    ),
                    actor=request.user,
                    installation_id=(
                        serializer
                        .validated_data[
                            "installation_id"
                        ]
                    ),
                    repository_id=(
                        serializer
                        .validated_data[
                            "repository_id"
                        ]
                    ),
                    is_primary=(
                        serializer
                        .validated_data[
                            "is_primary"
                        ]
                    ),
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
            GitHubAPIError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            WorkspaceGitHubRepositorySerializer(
                linked
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspaceGitHubRepositoryDetailView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        repository_link_id,
    ):
        linked = (
            self.get_linked_repository()
        )

        try:
            require_github_viewer(
                workspace=(
                    linked.workspace
                ),
                user=request.user,
            )

        except DjangoPermissionDenied as error:
            handle_service_error(
                error
            )

        return Response(
            WorkspaceGitHubRepositorySerializer(
                linked
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        repository_link_id,
    ):
        try:
            unlink_workspace_repository(
                linked_repository=(
                    self
                    .get_linked_repository()
                ),
                actor=request.user,
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
            ),
        )


class WorkspaceGitHubRepositoryPrimaryView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        repository_link_id,
    ):
        try:
            linked = (
                set_primary_repository(
                    linked_repository=(
                        self
                        .get_linked_repository()
                    ),
                    actor=request.user,
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            WorkspaceGitHubRepositorySerializer(
                linked
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceGitHubRepositorySyncView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        repository_link_id,
    ):
        try:
            linked = (
                sync_workspace_repository(
                    linked_repository=(
                        self
                        .get_linked_repository()
                    ),
                    actor=request.user,
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
            GitHubAPIError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            WorkspaceGitHubRepositorySerializer(
                linked
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceGitHubRepositoryOverviewView(
    WorkspaceGitHubMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        repository_link_id,
    ):
        try:
            overview = (
                get_repository_overview(
                    linked_repository=(
                        self
                        .get_linked_repository()
                    ),
                    user=request.user,
                )
            )

        except (
            DjangoPermissionDenied,
            DjangoValidationError,
            GitHubAPIError,
        ) as error:
            handle_service_error(
                error
            )

        return Response(
            overview,
            status=status.HTTP_200_OK,
        )


class GitHubSetupView(APIView):
    permission_classes = (
        AllowAny,
    )

    authentication_classes = ()

    def get(
        self,
        request,
    ):
        raw_state = (
            request.query_params.get(
                "state"
            )
        )

        installation_id = (
            request.query_params.get(
                "installation_id"
            )
        )

        setup_action = str(
            request.query_params.get(
                "setup_action"
            )
            or ""
        ).strip().lower()

        if not installation_id:
            return apply_sensitive_response_headers(
                Response(
                    {
                        "status": "error",
                        "code": (
                            "invalid_setup"
                        ),
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )
            )

        try:
            installation_id = int(
                installation_id
            )

            if installation_id <= 0:
                raise ValueError

        except (
            TypeError,
            ValueError,
        ):
            return apply_sensitive_response_headers(
                Response(
                    {
                        "status": "error",
                        "code": (
                            "invalid_setup"
                        ),
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )
            )

        # GitHubの「Redirect on update」では、
        # 既存Installation更新後にstateなしで
        # Setup URLへ戻ることがある。
        # このinstallation_idは信頼せず、
        # DBへの紐付け処理も行わない。
        if not raw_state:
            if setup_action == "update":
                return github_callback_response(
                    success=True,
                )

            return apply_sensitive_response_headers(
                Response(
                    {
                        "status": "error",
                        "code": (
                            "invalid_setup"
                        ),
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )
            )

        try:
            (
                client_id,
                callback_url,
            ) = (
                get_github_oauth_configuration()
            )

            state = (
                attach_installation_to_github_state(
                    raw_state=raw_state,
                    installation_id=(
                        installation_id
                    ),
                )
            )

            code_challenge = (
                build_github_pkce_challenge(
                    state
                )
            )

        except DjangoValidationError:
            return apply_sensitive_response_headers(
                Response(
                    {
                        "status": "error",
                        "code": (
                            "invalid_setup"
                        ),
                    },
                    status=(
                        status
                        .HTTP_400_BAD_REQUEST
                    ),
                )
            )

        authorization_url = (
            "https://github.com/"
            "login/oauth/authorize?"
            + urlencode(
                {
                    "client_id": (
                        client_id
                    ),
                    "redirect_uri": (
                        callback_url
                    ),
                    "state": raw_state,
                    "code_challenge": (
                        code_challenge
                    ),
                    "code_challenge_method": (
                        "S256"
                    ),
                }
            )
        )

        return apply_sensitive_response_headers(
            HttpResponseRedirect(
                authorization_url
            )
        )