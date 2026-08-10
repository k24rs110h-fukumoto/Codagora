from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsActiveCodagoraUser,
)
from workspaces.selectors import (
    get_accessible_workspaces,
)

from .pagination import (
    CalendarEventCursorPagination,
)
from .recurrence import expand_events
from .selectors import (
    get_workspace_calendar_events,
)
from .serializers import (
    CalendarEventSerializer,
    CalendarEventWriteSerializer,
    CalendarOccurrenceRangeSerializer,
    CalendarOccurrenceSerializer,
    CalendarParticipantResponseSerializer,
    CalendarParticipantSerializer,
)
from .services import (
    create_calendar_event,
    delete_calendar_event,
    respond_to_calendar_event,
    update_calendar_event,
)


def handle_service_error(error):
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
        raise ValidationError(
            {
                "detail": (
                    error.messages
                ),
            }
        ) from error

    raise error


class WorkspaceCalendarMixin:
    def get_workspace(self):
        return get_object_or_404(
            get_accessible_workspaces(
                user=self.request.user,
            ),
            slug=self.kwargs[
                "workspace_slug"
            ],
        )

    def get_event(self):
        workspace = (
            self.get_workspace()
        )

        return get_object_or_404(
            get_workspace_calendar_events(
                workspace=workspace,
            ),
            id=self.kwargs[
                "event_id"
            ],
        )


class CalendarEventListCreateView(
    WorkspaceCalendarMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    pagination_class = (
        CalendarEventCursorPagination
    )

    def get(
        self,
        request,
        workspace_slug,
    ):
        workspace = (
            self.get_workspace()
        )

        queryset = (
            get_workspace_calendar_events(
                workspace=workspace,
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
                CalendarEventSerializer(
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
        workspace = (
            self.get_workspace()
        )

        serializer = (
            CalendarEventWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            event = (
                create_calendar_event(
                    workspace=workspace,
                    actor=request.user,
                    data=dict(
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

        event = get_object_or_404(
            get_workspace_calendar_events(
                workspace=workspace,
            ),
            id=event.id,
        )

        return Response(
            CalendarEventSerializer(
                event
            ).data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class CalendarEventDetailView(
    WorkspaceCalendarMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def get(
        self,
        request,
        workspace_slug,
        event_id,
    ):
        return Response(
            CalendarEventSerializer(
                self.get_event()
            ).data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        workspace_slug,
        event_id,
    ):
        event = self.get_event()

        participant_ids = [
            participant.user_id
            for participant
            in (
                event.event_participants
                .all()
            )
        ]

        initial = {
            "title": event.title,
            "description": (
                event.description
            ),
            "location_name": (
                event.location_name
            ),
            "timezone": (
                event.timezone
            ),
            "is_all_day": (
                event.is_all_day
            ),
            "starts_at": (
                event.starts_at
            ),
            "ends_at": (
                event.ends_at
            ),
            "start_date": (
                event.start_date
            ),
            "end_date": (
                event.end_date
            ),
            "recurrence_frequency": (
                event
                .recurrence_frequency
            ),
            "recurrence_interval": (
                event
                .recurrence_interval
            ),
            "recurrence_weekdays": (
                event
                .recurrence_weekdays
            ),
            "recurrence_until": (
                event
                .recurrence_until
            ),
            "participant_ids": (
                participant_ids
            ),
        }

        initial.update(
            request.data
        )

        serializer = (
            CalendarEventWriteSerializer(
                data=initial,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            event = (
                update_calendar_event(
                    event=event,
                    actor=request.user,
                    data=dict(
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

        event = get_object_or_404(
            get_workspace_calendar_events(
                workspace=(
                    event.workspace
                ),
            ),
            id=event.id,
        )

        return Response(
            CalendarEventSerializer(
                event
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request,
        workspace_slug,
        event_id,
    ):
        try:
            delete_calendar_event(
                event=self.get_event(),
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


class CalendarOccurrenceListView(
    WorkspaceCalendarMixin,
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
            CalendarOccurrenceRangeSerializer(
                data=request.query_params,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        workspace = (
            self.get_workspace()
        )

        events = list(
            get_workspace_calendar_events(
                workspace=workspace,
            )
        )

        occurrences = expand_events(
            events=events,
            range_start=(
                serializer
                .validated_data[
                    "start"
                ]
            ),
            range_end=(
                serializer
                .validated_data[
                    "end"
                ]
            ),
        )

        return Response(
            CalendarOccurrenceSerializer(
                occurrences,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class CalendarParticipantResponseView(
    WorkspaceCalendarMixin,
    APIView,
):
    permission_classes = (
        IsActiveCodagoraUser,
    )

    def post(
        self,
        request,
        workspace_slug,
        event_id,
    ):
        serializer = (
            CalendarParticipantResponseSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            participant = (
                respond_to_calendar_event(
                    event=self.get_event(),
                    user=request.user,
                    response=(
                        serializer
                        .validated_data[
                            "response"
                        ]
                    ),
                )
            )

        except DjangoValidationError as error:
            handle_service_error(
                error
            )

        return Response(
            CalendarParticipantSerializer(
                participant
            ).data,
            status=status.HTTP_200_OK,
        )