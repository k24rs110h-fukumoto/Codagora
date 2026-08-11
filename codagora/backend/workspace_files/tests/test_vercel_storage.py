from types import SimpleNamespace
from unittest.mock import (
    MagicMock,
    patch,
)
from uuid import uuid4

from django.core.exceptions import (
    ImproperlyConfigured,
    SuspiciousFileOperation,
)
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import (
    SimpleTestCase,
    override_settings,
)

from vercel.blob import (
    BlobNotFoundError,
)

from workspace_files.vercel_storage import (
    VercelBlobStorage,
)


@override_settings(
    BLOB_READ_WRITE_TOKEN=(
        "vercel_blob_test_token"
    ),
)
class VercelBlobStorageTests(
    SimpleTestCase
):
    def build_path(self):
        workspace_id = uuid4()
        file_id = uuid4()

        return (
            "workspace_files/"
            f"{workspace_id}/"
            f"{file_id}/"
            "content.txt"
        )

    def configure_client(
        self,
        client_class,
    ):
        client = MagicMock()

        (
            client_class
            .return_value
            .__enter__
            .return_value
        ) = client

        return client

    @override_settings(
        BLOB_READ_WRITE_TOKEN="",
    )
    def test_token_is_required(
        self,
    ):
        with self.assertRaises(
            ImproperlyConfigured
        ):
            VercelBlobStorage()

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_save_uploads_private_blob(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        uploaded_file = (
            SimpleUploadedFile(
                "document.txt",
                b"Codagora Blob",
                content_type="text/plain",
            )
        )

        client.put.return_value = (
            SimpleNamespace(
                pathname=path,
            )
        )

        storage = (
            VercelBlobStorage()
        )

        saved_name = storage._save(
            path,
            uploaded_file,
        )

        self.assertEqual(
            saved_name,
            path,
        )

        client_class.assert_called_once_with(
            token=(
                "vercel_blob_test_token"
            )
        )

        client.put.assert_called_once_with(
            path,
            uploaded_file,
            access="private",
            content_type="text/plain",
            add_random_suffix=False,
            overwrite=False,
            multipart=False,
        )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_large_file_uses_multipart(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        uploaded_file = (
            MagicMock()
        )

        uploaded_file.size = (
            8 * 1024 * 1024
        )

        uploaded_file.content_type = (
            "application/octet-stream"
        )

        uploaded_file.seek = (
            MagicMock()
        )

        client.put.return_value = (
            SimpleNamespace(
                pathname=path,
            )
        )

        storage = (
            VercelBlobStorage()
        )

        storage._save(
            path,
            uploaded_file,
        )

        client.put.assert_called_once_with(
            path,
            uploaded_file,
            access="private",
            content_type=(
                "application/octet-stream"
            ),
            add_random_suffix=False,
            overwrite=False,
            multipart=True,
        )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_open_gets_private_blob(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        client.get.return_value = (
            SimpleNamespace(
                content=(
                    b"secure content"
                ),
            )
        )

        storage = (
            VercelBlobStorage()
        )

        file_handle = storage._open(
            path,
            mode="rb",
        )

        self.assertEqual(
            file_handle.read(),
            b"secure content",
        )

        client.get.assert_called_once_with(
            path,
            access="private",
            use_cache=True,
        )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_missing_blob_open_raises(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        client.get.side_effect = (
            BlobNotFoundError()
        )

        storage = (
            VercelBlobStorage()
        )

        with self.assertRaises(
            FileNotFoundError
        ):
            storage._open(
                path,
                mode="rb",
            )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_exists_returns_true(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        client.head.return_value = (
            SimpleNamespace(
                size=100,
            )
        )

        storage = (
            VercelBlobStorage()
        )

        self.assertTrue(
            storage.exists(
                path
            )
        )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_exists_returns_false(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        client.head.side_effect = (
            BlobNotFoundError()
        )

        storage = (
            VercelBlobStorage()
        )

        self.assertFalse(
            storage.exists(
                path
            )
        )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_size_uses_blob_head(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        client.head.return_value = (
            SimpleNamespace(
                size=12345,
            )
        )

        storage = (
            VercelBlobStorage()
        )

        self.assertEqual(
            storage.size(
                path
            ),
            12345,
        )

    @patch(
        "workspace_files."
        "vercel_storage."
        "BlobClient"
    )
    def test_delete_removes_blob(
        self,
        client_class,
    ):
        client = self.configure_client(
            client_class
        )

        path = self.build_path()

        storage = (
            VercelBlobStorage()
        )

        storage.delete(
            path
        )

        client.delete.assert_called_once_with(
            path
        )

    def test_url_points_to_secure_api(
        self,
    ):
        workspace_id = uuid4()
        file_id = uuid4()

        path = (
            "workspace_files/"
            f"{workspace_id}/"
            f"{file_id}/"
            "content.pdf"
        )

        storage = (
            VercelBlobStorage()
        )

        self.assertEqual(
            storage.url(
                path
            ),
            (
                "/api/v1/files/"
                f"{file_id}/"
                "download/"
            ),
        )

    def test_path_traversal_is_rejected(
        self,
    ):
        storage = (
            VercelBlobStorage()
        )

        with self.assertRaises(
            SuspiciousFileOperation
        ):
            storage.exists(
                "../secret.txt"
            )

    def test_invalid_url_path_is_rejected(
        self,
    ):
        storage = (
            VercelBlobStorage()
        )

        with self.assertRaises(
            ValueError
        ):
            storage.url(
                "other/file.txt"
            )