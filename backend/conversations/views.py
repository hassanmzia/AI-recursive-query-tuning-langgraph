"""Views for the conversations app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Session, Message, QueryRefinement
from .serializers import (
    SessionSerializer,
    SessionListSerializer,
    MessageSerializer,
    QueryRefinementSerializer,
)


class SessionViewSet(viewsets.ModelViewSet):
    """CRUD for conversation sessions."""

    queryset = Session.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return SessionListSerializer
        return SessionSerializer

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        session = self.get_object()
        messages = session.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def refinements(self, request, pk=None):
        session = self.get_object()
        refinements = session.refinements.all()
        serializer = QueryRefinementSerializer(refinements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_message(self, request, pk=None):
        session = self.get_object()
        data = request.data.copy()
        data["session"] = session.id
        serializer = MessageSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Auto-generate title from first user message
        if not session.title and data.get("role") == "user":
            session.title = data["content"][:100]
            session.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of messages."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filterset_fields = ["session", "role"]
