import mimetypes

from pathlib import PurePosixPath
from uuid import UUID

from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
    SuspiciousFileOperation,
)
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.urls import reverse

from vercel.blob import (
    BlobClient,
    BlobNotFoundError,
)


class VercelBlobStorage(Storage):
    multipart_threshold = (
        8 * 1024 * 1024
    )

    def __init__(
        self,
        token=None,
    ):
        configured_token = (
            token
            if token is not None
            else getattr(
                settings,
                "BLOB_READ_WRITE_TOKEN",
                "",
            )
        )

        self.token = str(
            configured_token
            or ""
        ).strip()

        if not self.token:
            raise ImproperlyConfigured(
                "BLOB_READ_WRITE_TOKEN "
                "is not configured."
            )

    def _normalize_name(
        self,
        name,
    ):
        raw_name = str(
            name
            or ""
        ).replace(
            "\\",
            "/",
        )

        if not raw_name:
            raise SuspiciousFileOperation(
                "Empty storage path "
                "is not allowed."
            )

        if raw_name.startswith("/"):
            raise SuspiciousFileOperation(
                "Absolute storage paths "
                "are not allowed."
            )

        raw_parts = (
            raw_name.split("/")
        )

        if any(
            part in (
                "",
                ".",
                "..",
            )
            for part in raw_parts
        ):
            raise SuspiciousFileOperation(
                "Invalid storage path."
            )

        path = PurePosixPath(
            raw_name
        )

        if path.is_absolute():
            raise SuspiciousFileOperation(
                "Absolute storage paths "
                "are not allowed."
            )

        return path.as_posix()

    def _get_content_type(
        self,
        *,
        content,
        name,
    ):
        content_type = getattr(
            content,
            "content_type",
            None,
        )

        if content_type:
            return content_type

        guessed_type = (
            mimetypes.guess_type(
                name
            )[0]
        )

        return (
            guessed_type
            or "application/octet-stream"
        )

    def _should_use_multipart(
        self,
        content,
    ):
        size = getattr(
            content,
            "size",
            None,
        )

        if size is None:
            return False

        return (
            size
            >= self.multipart_threshold
        )

    def _save(
        self,
        name,
        content,
    ):
        normalized_name = (
            self._normalize_name(
                name
            )
        )

        if hasattr(
            content,
            "seek",
        ):
            content.seek(0)

        content_type = (
            self._get_content_type(
                content=content,
                name=normalized_name,
            )
        )

        multipart = (
            self._should_use_multipart(
                content
            )
        )

        with BlobClient(
            token=self.token
        ) as client:
            result = client.put(
                normalized_name,
                content,
                access="private",
                content_type=(
                    content_type
                ),
                add_random_suffix=False,
                overwrite=False,
                multipart=multipart,
            )

        pathname = getattr(
            result,
            "pathname",
            None,
        )

        if not pathname:
            raise OSError(
                "Vercel Blob did not "
                "return a pathname."
            )

        return self._normalize_name(
            pathname
        )

    def _open(
        self,
        name,
        mode="rb",
    ):
        if mode not in (
            "rb",
            "r",
        ):
            raise ValueError(
                "Vercel Blob storage "
                "supports read-only open()."
            )

        normalized_name = (
            self._normalize_name(
                name
            )
        )

        try:
            with BlobClient(
                token=self.token
            ) as client:
                result = client.get(
                    normalized_name,
                    access="private",
                    use_cache=True,
                )

        except BlobNotFoundError as error:
            raise FileNotFoundError(
                normalized_name
            ) from error

        if result is None:
            raise FileNotFoundError(
                normalized_name
            )

        content = getattr(
            result,
            "content",
            None,
        )

        if content is None:
            raise FileNotFoundError(
                normalized_name
            )

        return ContentFile(
            content,
            name=normalized_name,
        )

    def exists(
        self,
        name,
    ):
        normalized_name = (
            self._normalize_name(
                name
            )
        )

        try:
            with BlobClient(
                token=self.token
            ) as client:
                result = client.head(
                    normalized_name
                )

        except BlobNotFoundError:
            return False

        return result is not None

    def delete(
        self,
        name,
    ):
        if not name:
            return

        normalized_name = (
            self._normalize_name(
                name
            )
        )

        try:
            with BlobClient(
                token=self.token
            ) as client:
                client.delete(
                    normalized_name
                )

        except BlobNotFoundError:
            return

    def size(
        self,
        name,
    ):
        normalized_name = (
            self._normalize_name(
                name
            )
        )

        try:
            with BlobClient(
                token=self.token
            ) as client:
                result = client.head(
                    normalized_name
                )

        except BlobNotFoundError as error:
            raise FileNotFoundError(
                normalized_name
            ) from error

        if result is None:
            raise FileNotFoundError(
                normalized_name
            )

        return int(
            result.size
        )

    def url(
        self,
        name,
    ):
        normalized_name = (
            self._normalize_name(
                name
            )
        )

        parts = (
            normalized_name
            .split("/")
        )

        if (
            len(parts) != 4
            or parts[0]
            != "workspace_files"
        ):
            raise ValueError(
                "Invalid workspace file "
                "storage path."
            )

        try:
            file_id = UUID(
                parts[2]
            )

        except ValueError as error:
            raise ValueError(
                "Invalid workspace file ID."
            ) from error

        return reverse(
            "workspace_file_downloads:download",
            kwargs={
                "file_id": file_id,
            },
        )