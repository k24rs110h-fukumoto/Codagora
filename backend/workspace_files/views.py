from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.http import FileResponse
from django.shortcuts import (
    get_object_or_404,
)

from rest_framework import status
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.response import (
    Response,
)
from rest_framework.views import (
    APIView,
)

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from workspaces.models import (
    WorkspaceMember,
)
from workspaces.selectors import (
    get_accessible_workspaces,
)

from .models import (
    WorkspaceFile,
    WorkspaceFolder,
)
from .pagination import (
    WorkspaceFileCursorPagination,
)
from .selectors import (
    get_deleted_workspace_files,
    get_deleted_workspace_folders,
    get_workspace_files,
    get_workspace_folders,
)
from .serializers import (
    WorkspaceFileSerializer,
    WorkspaceFileUpdateSerializer,
    WorkspaceFileUploadSerializer,
    WorkspaceFolderCreateSerializer,
    WorkspaceFolderSerializer,
    WorkspaceFolderUpdateSerializer,
    WorkspaceLocationQuerySerializer,
)
from .services import (
    create_workspace_folder,
    delete_workspace_file,
    delete_workspace_folder,
    get_workspace_role,
    restore_workspace_file,
    restore_workspace_folder,
    update_workspace_file,
    update_workspace_folder,
    upload_workspace_file,
)


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

    raise error


class WorkspaceStorageMixin:
    def get_workspace(self):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=self.kwargs[
                "workspace_slug"
            ],
        )

    def get_active_folder(
        self,
        folder_id=None,
    ):
        if folder_id is None:
            folder_id = self.kwargs[
                "folder_id"
            ]

        return get_object_or_404(
            WorkspaceFolder.objects
            .select_related(
                "workspace",
                "parent",
                "created_by",
            ),
            id=folder_id,
            workspace=(
                self.get_workspace()
            ),
            deleted_at__isnull=True,
        )

    def get_deleted_folder(self):
        return get_object_or_404(
            WorkspaceFolder.objects
            .select_related(
                "workspace",
                "parent",
                "created_by",
            ),
            id=self.kwargs[
                "folder_id"
            ],
            workspace=(
                self.get_workspace()
            ),
            deleted_at__isnull=False,
        )

    def get_active_file(self):
        return get_object_or_404(
            WorkspaceFile.objects
            .select_related(
                "workspace",
                "folder",
                "uploaded_by",
            ),
            id=self.kwargs[
                "file_id"
            ],
            workspace=(
                self.get_workspace()
            ),
            deleted_at__isnull=True,
        )

    def get_deleted_file(self):
        return get_object_or_404(
            WorkspaceFile.objects
            .select_related(
                "workspace",
                "folder",
                "uploaded_by",
            ),
            id=self.kwargs[
                "file_id"
            ],
            workspace=(
                self.get_workspace()
            ),
            deleted_at__isnull=False,
        )


class WorkspaceFolderListCreateView(
    WorkspaceStorageMixin,
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
        serializer = (
            WorkspaceLocationQuerySerializer(
                data=request.query_params,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        workspace = (
            self.get_workspace()
        )

        parent = None

        parent_id = (
            serializer
            .validated_data
            .get("folder_id")
        )

        if parent_id:
            parent = get_object_or_404(
                WorkspaceFolder.objects,
                id=parent_id,
                workspace=workspace,
                deleted_at__isnull=True,
            )

        folders = (
            get_workspace_folders(
                workspace=workspace,
                parent=parent,
            )
        )

        return Response(
            WorkspaceFolderSerializer(
                folders,
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
            WorkspaceFolderCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            folder = (
                create_workspace_folder(
                    workspace=(
                        self.get_workspace()
                    ),
                    actor=request.user,
                    name=(
                        serializer
                        .validated_data[
                            "name"
                        ]
                    ),
                    parent_id=(
                        serializer
                        .validated_data
                        .get(
                            "parent_id"
                        )
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

        return Response(
            WorkspaceFolderSerializer(
                folder
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspaceFolderDetailView(
    WorkspaceStorageMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        folder_id,
    ):
        return Response(
            WorkspaceFolderSerializer(
                self.get_active_folder()
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        workspace_slug,
        folder_id,
    ):
        serializer = (
            WorkspaceFolderUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            folder = (
                update_workspace_folder(
                    folder=(
                        self
                        .get_active_folder()
                    ),
                    actor=request.user,
                    changes=dict(
                        serializer
                        .validated_data
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

        return Response(
            WorkspaceFolderSerializer(
                folder
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        folder_id,
    ):
        try:
            delete_workspace_folder(
                folder=(
                    self.get_active_folder()
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


class WorkspaceFolderRestoreView(
    WorkspaceStorageMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        folder_id,
    ):
        try:
            folder = (
                restore_workspace_folder(
                    folder=(
                        self
                        .get_deleted_folder()
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
            WorkspaceFolderSerializer(
                folder
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceFileListCreateView(
    WorkspaceStorageMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    pagination_class = (
        WorkspaceFileCursorPagination
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        query_serializer = (
            WorkspaceLocationQuerySerializer(
                data=request.query_params,
            )
        )

        query_serializer.is_valid(
            raise_exception=True,
        )

        workspace = (
            self.get_workspace()
        )

        folder = None

        folder_id = (
            query_serializer
            .validated_data
            .get("folder_id")
        )

        if folder_id:
            folder = get_object_or_404(
                WorkspaceFolder.objects,
                id=folder_id,
                workspace=workspace,
                deleted_at__isnull=True,
            )

        queryset = (
            get_workspace_files(
                workspace=workspace,
                folder=folder,
            )
        )

        paginator = (
            self.pagination_class()
        )

        page = (
            paginator.paginate_queryset(
                queryset,
                request,
                view=self,
            )
        )

        return (
            paginator
            .get_paginated_response(
                WorkspaceFileSerializer(
                    page,
                    many=True,
                ).data
            )
        )

    def post(
        self,
        request,
        workspace_slug,
    ):
        serializer = (
            WorkspaceFileUploadSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            workspace_file = (
                upload_workspace_file(
                    workspace=(
                        self.get_workspace()
                    ),
                    actor=request.user,
                    uploaded_file=(
                        serializer
                        .validated_data[
                            "file"
                        ]
                    ),
                    folder_id=(
                        serializer
                        .validated_data
                        .get(
                            "folder_id"
                        )
                    ),
                    display_name=(
                        serializer
                        .validated_data
                        .get(
                            "display_name"
                        )
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

        return Response(
            WorkspaceFileSerializer(
                workspace_file
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class WorkspaceFileDetailView(
    WorkspaceStorageMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        file_id,
    ):
        return Response(
            WorkspaceFileSerializer(
                self.get_active_file()
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        workspace_slug,
        file_id,
    ):
        serializer = (
            WorkspaceFileUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            workspace_file = (
                update_workspace_file(
                    workspace_file=(
                        self
                        .get_active_file()
                    ),
                    actor=request.user,
                    changes=dict(
                        serializer
                        .validated_data
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

        return Response(
            WorkspaceFileSerializer(
                workspace_file
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        file_id,
    ):
        try:
            delete_workspace_file(
                workspace_file=(
                    self.get_active_file()
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


class WorkspaceFileRestoreView(
    WorkspaceStorageMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        file_id,
    ):
        try:
            workspace_file = (
                restore_workspace_file(
                    workspace_file=(
                        self
                        .get_deleted_file()
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
            WorkspaceFileSerializer(
                workspace_file
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceFileDownloadView(
    WorkspaceStorageMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        file_id,
    ):
        workspace_file = (
            self.get_active_file()
        )

        storage = (
            workspace_file
            .file
            .storage
        )

        file_name = (
            workspace_file
            .file
            .name
        )

        if (
            not file_name
            or not storage.exists(
                file_name
            )
        ):
            raise NotFound(
                "ファイル本体が"
                "見つかりません。"
            )

        opened_file = (
            workspace_file
            .file
            .open("rb")
        )

        response = FileResponse(
            opened_file,
            as_attachment=True,
            filename=(
                workspace_file
                .display_name
            ),
        )

        response[
            "X-Content-Type-Options"
        ] = "nosniff"

        return response


class WorkspaceTrashView(
    WorkspaceStorageMixin,
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

        role = get_workspace_role(
            workspace=workspace,
            user=request.user,
        )

        if role == (
            WorkspaceMember.Role.GUEST
        ):
            raise PermissionDenied(
                "GuestはTrashを"
                "閲覧できません。"
            )

        folders = (
            get_deleted_workspace_folders(
                workspace=workspace,
            )
        )

        files = (
            get_deleted_workspace_files(
                workspace=workspace,
            )
        )

        if role not in (
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        ):
            folders = folders.filter(
                created_by=request.user,
            )

            files = files.filter(
                uploaded_by=request.user,
            )

        return Response(
            {
                "folders": (
                    WorkspaceFolderSerializer(
                        folders,
                        many=True,
                    ).data
                ),
                "files": (
                    WorkspaceFileSerializer(
                        files,
                        many=True,
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )