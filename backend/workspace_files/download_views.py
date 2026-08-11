from django.http import FileResponse

from rest_framework.exceptions import (
    NotFound,
)
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)

from .downloads import (
    get_workspace_file_for_download,
)


class WorkspaceFileDownloadView(
    APIView
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        file_id,
    ):
        workspace_file = (
            get_workspace_file_for_download(
                file_id=file_id,
                user=request.user,
            )
        )

        field_file = (
            workspace_file.file
        )

        storage = (
            field_file.storage
        )

        try:
            file_handle = storage.open(
                field_file.name,
                mode="rb",
            )

        except FileNotFoundError as error:
            raise NotFound(
                detail=(
                    "保存されたファイルが"
                    "見つかりません。"
                )
            ) from error

        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=(
                workspace_file
                .display_name
            ),
            content_type=(
                workspace_file
                .content_type
                or (
                    "application/"
                    "octet-stream"
                )
            ),
        )

        response[
            "Cache-Control"
        ] = (
            "private, no-store"
        )

        response[
            "Pragma"
        ] = "no-cache"

        response[
            "X-Content-Type-Options"
        ] = "nosniff"

        return response