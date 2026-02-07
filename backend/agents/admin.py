"""Admin configuration for the agents app."""
from django.contrib import admin
from .models import AgentConfig, WorkflowExecution, AgentInteraction, MCPToolRegistration, A2AMessage


@admin.register(AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "agent_type", "model_name", "is_active", "created_at"]
    list_filter = ["agent_type", "is_active"]
    search_fields = ["name", "description"]


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ["id", "workflow_type", "status", "input_query", "duration_ms", "created_at"]
    list_filter = ["status", "workflow_type"]
    search_fields = ["input_query", "final_answer"]
    readonly_fields = ["execution_trace", "nodes_visited"]


@admin.register(AgentInteraction)
class AgentInteractionAdmin(admin.ModelAdmin):
    list_display = ["agent_name", "node_name", "iteration", "duration_ms", "created_at"]
    list_filter = ["agent_name", "node_name"]


@admin.register(MCPToolRegistration)
class MCPToolRegistrationAdmin(admin.ModelAdmin):
    list_display = ["tool_name", "is_active", "created_at"]
    list_filter = ["is_active"]


@admin.register(A2AMessage)
class A2AMessageAdmin(admin.ModelAdmin):
    list_display = ["sender_agent", "receiver_agent", "message_type", "created_at"]
    list_filter = ["message_type"]
