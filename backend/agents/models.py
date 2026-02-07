"""Models for the multi-agent system."""
import uuid
from django.db import models
from django.utils import timezone


class AgentConfig(models.Model):
    """Configuration for an AI agent in the multi-agent system."""

    AGENT_TYPES = [
        ("react_researcher", "ReAct Research Agent"),
        ("qa_specialist", "QA Specialist Agent"),
        ("critique", "Critique Agent"),
        ("summarizer", "Summarization Agent"),
        ("query_rewriter", "Query Rewriter Agent"),
        ("orchestrator", "Orchestrator Agent"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    description = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, default="gpt-4o-mini")
    temperature = models.FloatField(default=0.0)
    max_tokens = models.IntegerField(default=500)
    top_p = models.FloatField(default=0.95)
    frequency_penalty = models.FloatField(default=1.2)
    system_prompt = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_agent_type_display()})"


class WorkflowExecution(models.Model):
    """Tracks execution of LangGraph workflows."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_type = models.CharField(max_length=100, default="recursive_qa")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    input_query = models.TextField()
    final_answer = models.TextField(blank=True)
    total_iterations = models.IntegerField(default=0)
    max_iterations = models.IntegerField(default=5)
    nodes_visited = models.JSONField(default=list)
    execution_trace = models.JSONField(default=list)
    mermaid_diagram = models.TextField(blank=True)
    langsmith_run_id = models.CharField(max_length=255, blank=True)
    langfuse_trace_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Workflow {self.id} - {self.status}"

    def start(self):
        self.status = "running"
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete(self, answer, trace):
        self.status = "completed"
        self.final_answer = answer
        self.execution_trace = trace
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_ms = int(
                (self.completed_at - self.started_at).total_seconds() * 1000
            )
        self.save()

    def fail(self, error):
        self.status = "failed"
        self.error_message = str(error)
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_ms = int(
                (self.completed_at - self.started_at).total_seconds() * 1000
            )
        self.save()


class AgentInteraction(models.Model):
    """Records individual agent interactions within a workflow."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    agent_name = models.CharField(max_length=100)
    node_name = models.CharField(max_length=100)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    decision = models.CharField(max_length=100, blank=True)
    iteration = models.IntegerField(default=0)
    duration_ms = models.IntegerField(null=True, blank=True)
    token_usage = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.agent_name}:{self.node_name} @ iteration {self.iteration}"


class MCPToolRegistration(models.Model):
    """Registry for MCP (Model Context Protocol) tools."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tool_name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    input_schema = models.JSONField(default=dict)
    endpoint = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tool_name"]

    def __str__(self):
        return self.tool_name


class A2AMessage(models.Model):
    """Agent-to-Agent protocol messages."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="a2a_messages",
        null=True,
        blank=True,
    )
    sender_agent = models.CharField(max_length=100)
    receiver_agent = models.CharField(max_length=100)
    message_type = models.CharField(
        max_length=50,
        choices=[
            ("task_request", "Task Request"),
            ("task_response", "Task Response"),
            ("feedback", "Feedback"),
            ("delegation", "Delegation"),
            ("status_update", "Status Update"),
        ],
    )
    payload = models.JSONField(default=dict)
    correlation_id = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_agent} -> {self.receiver_agent}: {self.message_type}"
