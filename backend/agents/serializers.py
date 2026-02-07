"""Serializers for the agents app."""
from rest_framework import serializers
from .models import (
    AgentConfig,
    WorkflowExecution,
    AgentInteraction,
    MCPToolRegistration,
    A2AMessage,
)


class AgentConfigSerializer(serializers.ModelSerializer):
    agent_type_display = serializers.CharField(
        source="get_agent_type_display", read_only=True
    )

    class Meta:
        model = AgentConfig
        fields = "__all__"


class AgentInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentInteraction
        fields = "__all__"


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    interactions = AgentInteractionSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = "__all__"


class WorkflowExecutionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecution
        fields = [
            "id", "workflow_type", "status", "input_query",
            "total_iterations", "duration_ms", "created_at",
        ]


class MCPToolRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCPToolRegistration
        fields = "__all__"


class A2AMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = A2AMessage
        fields = "__all__"


class QueryInputSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=2000)
    workflow_type = serializers.ChoiceField(
        choices=["recursive_qa", "multi_agent"],
        default="recursive_qa",
    )
    max_iterations = serializers.IntegerField(default=5, min_value=1, max_value=10)
    session_id = serializers.CharField(required=False, allow_blank=True)


class MCPToolCallSerializer(serializers.Serializer):
    tool_name = serializers.CharField(max_length=255)
    arguments = serializers.DictField()
