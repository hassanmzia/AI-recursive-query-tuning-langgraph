"""Serializers for the conversations app."""
from rest_framework import serializers
from .models import Session, Message, QueryRefinement


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class QueryRefinementSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryRefinement
        fields = "__all__"


class SessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    refinements = QueryRefinementSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = "__all__"

    def get_message_count(self, obj):
        return obj.messages.count()


class SessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ["id", "title", "is_active", "message_count", "last_message", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last:
            return {"role": last.role, "content": last.content[:100], "created_at": last.created_at}
        return None
