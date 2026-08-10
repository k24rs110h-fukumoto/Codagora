from django.core.files.storage import (
    FileSystemStorage,
)
from django.http import (
    FileResponse,
    HttpResponseRedirect,
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

        if isinstance(
            storage,
            FileSystemStorage,
        ):
            file_handle = storage.open(
                field_file.name,
                mode="rb",
            )

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
                "X-Content-Type-Options"
            ] = "nosniff"

            return response

        download_url = storage.url(
            field_file.name
        )

        response = HttpResponseRedirect(
            download_url
        )

        response[
            "Cache-Control"
        ] = (
            "private, no-store"
        )

        response[
            "X-Content-Type-Options"
        ] = "nosniff"

        return response