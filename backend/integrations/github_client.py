from datetime import timedelta
from pathlib import Path

import jwt
import requests

from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
    ValidationError,
)
from django.utils import timezone

from .crypto import (
    decrypt_secret,
    encrypt_secret,
)


class GitHubAPIError(Exception):
    def __init__(
        self,
        message,
        status_code=None,
    ):
        super().__init__(message)

        self.status_code = (
            status_code
        )


def get_github_private_key():
    inline_key = (
        settings
        .GITHUB_APP_PRIVATE_KEY
    )

    if inline_key:
        return (
            inline_key
            .replace(
                "\\n",
                "\n",
            )
        )

    path_value = (
        settings
        .GITHUB_APP_PRIVATE_KEY_PATH
    )

    if not path_value:
        raise ImproperlyConfigured(
            "GitHub App private key is "
            "not configured."
        )

    path = (
        Path(path_value)
        .expanduser()
    )

    if not path.exists():
        raise ImproperlyConfigured(
            "GitHub App private key file "
            "does not exist."
        )

    return path.read_text(
        encoding="utf-8"
    )


def build_github_app_jwt():
    client_id = (
        settings
        .GITHUB_APP_CLIENT_ID
    )

    if not client_id:
        raise ImproperlyConfigured(
            "GITHUB_APP_CLIENT_ID "
            "is not configured."
        )

    now = timezone.now()

    payload = {
        "iat": int(
            (
                now
                - timedelta(
                    seconds=60
                )
            ).timestamp()
        ),
        "exp": int(
            (
                now
                + timedelta(
                    minutes=9
                )
            ).timestamp()
        ),
        "iss": client_id,
    }

    return jwt.encode(
        payload,
        get_github_private_key(),
        algorithm="RS256",
    )


def github_headers(
    token=None,
):
    headers = {
        "Accept": (
            "application/vnd.github+json"
        ),
        "X-GitHub-Api-Version": (
            settings.GITHUB_API_VERSION
        ),
        "User-Agent": (
            "Codagora"
        ),
    }

    if token:
        headers[
            "Authorization"
        ] = f"Bearer {token}"

    return headers


def github_request(
    method,
    path,
    *,
    token=None,
    params=None,
    json=None,
):
    url = (
        f"{settings.GITHUB_API_BASE_URL}"
        f"{path}"
    )

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=github_headers(
                token
            ),
            params=params,
            json=json,
            timeout=15,
        )

    except requests.RequestException as error:
        raise GitHubAPIError(
            "GitHub APIへ接続できません。"
        ) from error

    if response.status_code >= 400:
        try:
            payload = response.json()

            message = payload.get(
                "message",
                "GitHub API request failed.",
            )

        except ValueError:
            message = (
                "GitHub API request failed."
            )

        raise GitHubAPIError(
            message,
            status_code=(
                response.status_code
            ),
        )

    if response.status_code == 204:
        return None

    try:
        return response.json()

    except ValueError as error:
        raise GitHubAPIError(
            "GitHub API response is invalid."
        ) from error


def exchange_code_for_user_token(
    *,
    code,
    code_verifier=None,
):
    data = {
        "client_id": (
            settings
            .GITHUB_APP_CLIENT_ID
        ),
        "client_secret": (
            settings
            .GITHUB_APP_CLIENT_SECRET
        ),
        "code": code,
        "redirect_uri": (
            settings
            .GITHUB_APP_CALLBACK_URL
        ),
    }

    if code_verifier:
        data[
            "code_verifier"
        ] = code_verifier

    try:
        response = requests.post(
            (
                "https://github.com/"
                "login/oauth/access_token"
            ),
            headers={
                "Accept": (
                    "application/json"
                ),
                "User-Agent": (
                    "Codagora"
                ),
            },
            data=data,
            timeout=15,
        )

    except requests.RequestException as error:
        raise GitHubAPIError(
            "GitHub OAuthへ接続"
            "できません。"
        ) from error

    try:
        payload = response.json()

    except ValueError as error:
        raise GitHubAPIError(
            "GitHub OAuth response "
            "is invalid."
        ) from error

    if (
        response.status_code >= 400
        or payload.get("error")
    ):
        raise GitHubAPIError(
            payload.get(
                "error_description",
                payload.get(
                    "error",
                    "GitHub OAuth failed.",
                ),
            ),
            status_code=(
                response.status_code
            ),
        )

    if not payload.get(
        "access_token"
    ):
        raise GitHubAPIError(
            "GitHub access token "
            "was not returned."
        )

    return payload


def refresh_github_user_token(
    refresh_token,
):
    try:
        response = requests.post(
            (
                "https://github.com/"
                "login/oauth/access_token"
            ),
            headers={
                "Accept": (
                    "application/json"
                ),
                "User-Agent": (
                    "Codagora"
                ),
            },
            data={
                "client_id": (
                    settings
                    .GITHUB_APP_CLIENT_ID
                ),
                "client_secret": (
                    settings
                    .GITHUB_APP_CLIENT_SECRET
                ),
                "grant_type": (
                    "refresh_token"
                ),
                "refresh_token": (
                    refresh_token
                ),
            },
            timeout=15,
        )

    except requests.RequestException as error:
        raise GitHubAPIError(
            "GitHub Tokenを"
            "更新できません。"
        ) from error

    try:
        payload = response.json()

    except ValueError as error:
        raise GitHubAPIError(
            "GitHub Token response "
            "is invalid."
        ) from error

    if (
        response.status_code >= 400
        or payload.get("error")
    ):
        raise GitHubAPIError(
            payload.get(
                "error_description",
                "GitHub再接続が必要です。",
            ),
            status_code=(
                response.status_code
            ),
        )

    return payload


def apply_token_payload(
    *,
    connection,
    payload,
):
    now = timezone.now()

    access_token = payload.get(
        "access_token"
    )

    if not access_token:
        raise GitHubAPIError(
            "GitHub access token "
            "is missing."
        )

    connection.access_token_encrypted = (
        encrypt_secret(
            access_token
        )
    )

    expires_in = payload.get(
        "expires_in"
    )

    if expires_in:
        connection.access_token_expires_at = (
            now
            + timedelta(
                seconds=int(
                    expires_in
                )
            )
        )

    else:
        connection.access_token_expires_at = (
            None
        )

    refresh_token = payload.get(
        "refresh_token"
    )

    if refresh_token:
        connection.refresh_token_encrypted = (
            encrypt_secret(
                refresh_token
            )
        )

        refresh_expires_in = payload.get(
            "refresh_token_expires_in"
        )

        if refresh_expires_in:
            connection.refresh_token_expires_at = (
                now
                + timedelta(
                    seconds=int(
                        refresh_expires_in
                    )
                )
            )

    connection.token_type = (
        payload.get(
            "token_type",
            "bearer",
        )
    )

    connection.scope = (
        payload.get(
            "scope",
            "",
        )
    )


def get_valid_user_access_token(
    connection,
):
    now = timezone.now()

    expires_at = (
        connection
        .access_token_expires_at
    )

    if (
        expires_at is None
        or expires_at
        > now
        + timedelta(
            minutes=2
        )
    ):
        return decrypt_secret(
            connection
            .access_token_encrypted
        )

    refresh_expires_at = (
        connection
        .refresh_token_expires_at
    )

    if (
        not connection
        .refresh_token_encrypted
        or (
            refresh_expires_at
            and refresh_expires_at
            <= now
        )
    ):
        raise ValidationError(
            "GitHubとの再接続が"
            "必要です。"
        )

    refresh_token = decrypt_secret(
        connection
        .refresh_token_encrypted
    )

    payload = (
        refresh_github_user_token(
            refresh_token
        )
    )

    apply_token_payload(
        connection=connection,
        payload=payload,
    )

    connection.save(
        update_fields=(
            "access_token_encrypted",
            "access_token_expires_at",
            "refresh_token_encrypted",
            "refresh_token_expires_at",
            "token_type",
            "scope",
            "updated_at",
        )
    )

    return decrypt_secret(
        connection
        .access_token_encrypted
    )


def get_authenticated_github_user(
    access_token,
):
    return github_request(
        "GET",
        "/user",
        token=access_token,
    )


def list_user_installations(
    access_token,
):
    installations = []

    for page in range(
        1,
        11,
    ):
        payload = github_request(
            "GET",
            "/user/installations",
            token=access_token,
            params={
                "per_page": 100,
                "page": page,
            },
        )

        batch = payload.get(
            "installations",
            [],
        )

        installations.extend(
            batch
        )

        if len(batch) < 100:
            break

    return installations


def list_user_installation_repositories(
    *,
    access_token,
    installation_id,
):
    repositories = []

    for page in range(
        1,
        11,
    ):
        payload = github_request(
            "GET",
            (
                "/user/installations/"
                f"{installation_id}/"
                "repositories"
            ),
            token=access_token,
            params={
                "per_page": 100,
                "page": page,
            },
        )

        batch = payload.get(
            "repositories",
            [],
        )

        repositories.extend(
            batch
        )

        if len(batch) < 100:
            break

    return repositories


def get_installation_access_token(
    *,
    installation_id,
    repository_id=None,
):
    app_jwt = (
        build_github_app_jwt()
    )

    body = {}

    if repository_id:
        body[
            "repository_ids"
        ] = [
            int(repository_id)
        ]

    payload = github_request(
        "POST",
        (
            "/app/installations/"
            f"{installation_id}/"
            "access_tokens"
        ),
        token=app_jwt,
        json=body,
    )

    token = payload.get(
        "token"
    )

    if not token:
        raise GitHubAPIError(
            "Installation token "
            "was not returned."
        )

    return token