"""Views for the agents app."""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from .models import (
    AgentConfig,
    WorkflowExecution,
    AgentInteraction,
    MCPToolRegistration,
    A2AMessage,
)
from .serializers import (
    AgentConfigSerializer,
    WorkflowExecutionSerializer,
    WorkflowExecutionListSerializer,
    AgentInteractionSerializer,
    MCPToolRegistrationSerializer,
    A2AMessageSerializer,
    QueryInputSerializer,
    MCPToolCallSerializer,
)

logger = logging.getLogger(__name__)


def _get_workflow_engine():
    """Get or create the shared workflow engine."""
    from .apps import get_workflow_engine
    return get_workflow_engine()


def _get_multi_agent_orchestrator():
    """Get or create the multi-agent orchestrator."""
    from .apps import get_multi_agent_orchestrator
    return get_multi_agent_orchestrator()


def _get_mcp_server():
    """Get the MCP server instance."""
    from .apps import get_mcp_server
    return get_mcp_server()


def _get_a2a_handler():
    """Get the A2A protocol handler instance."""
    from .apps import get_a2a_handler
    return get_a2a_handler()


class AgentConfigViewSet(viewsets.ModelViewSet):
    """CRUD for agent configurations."""

    queryset = AgentConfig.objects.all()
    serializer_class = AgentConfigSerializer


class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of workflow executions."""

    queryset = WorkflowExecution.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return WorkflowExecutionListSerializer
        return WorkflowExecutionSerializer

    @action(detail=True, methods=["get"])
    def trace(self, request, pk=None):
        """Get the execution trace for a workflow."""
        execution = self.get_object()
        return Response({
            "execution_id": str(execution.id),
            "trace": execution.execution_trace,
            "nodes_visited": execution.nodes_visited,
            "mermaid_diagram": execution.mermaid_diagram,
        })


class ExecuteQueryView(APIView):
    """Execute a query through the AI workflow."""

    def post(self, request):
        serializer = QueryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"]
        workflow_type = serializer.validated_data.get("workflow_type", "recursive_qa")
        max_iterations = serializer.validated_data.get("max_iterations", 5)
        session_id = serializer.validated_data.get("session_id", "")

        # Create execution record
        execution = WorkflowExecution.objects.create(
            workflow_type=workflow_type,
            input_query=query,
            max_iterations=max_iterations,
        )
        execution.start()

        try:
            if workflow_type == "recursive_qa":
                engine = _get_workflow_engine()
                if engine is None:
                    execution.fail("Workflow engine not initialized. Check vector store.")
                    return Response(
                        {"error": "Workflow engine not initialized"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                result = engine.execute_sync(query, session_id=session_id)
                execution.complete(
                    answer=result["answer"],
                    trace=result["trace"],
                )
                execution.mermaid_diagram = engine.get_mermaid_diagram()
                execution.langfuse_trace_id = result.get("langfuse_trace_id", "")
                execution.save()

            elif workflow_type == "multi_agent":
                orchestrator = _get_multi_agent_orchestrator()
                if orchestrator is None:
                    execution.fail("Multi-agent orchestrator not initialized")
                    return Response(
                        {"error": "Multi-agent orchestrator not initialized"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                result = orchestrator.execute(query)
                execution.complete(
                    answer=result["answer"],
                    trace=result["agent_trace"],
                )
                execution.total_iterations = result.get("iterations", 0)
                execution.save()

            else:
                execution.fail(f"Unknown workflow type: {workflow_type}")
                return Response(
                    {"error": f"Unknown workflow type: {workflow_type}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({
                "execution_id": str(execution.id),
                "status": execution.status,
                "answer": execution.final_answer,
                "workflow_type": workflow_type,
                "duration_ms": execution.duration_ms,
                "trace": execution.execution_trace,
                "mermaid_diagram": execution.mermaid_diagram,
                "messages": result.get("messages", []),
                "summary": result.get("summary", ""),
                "critique_score": result.get("critique_score"),
            })

        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            execution.fail(str(e))
            return Response(
                {"error": str(e), "execution_id": str(execution.id)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WorkflowVisualizationView(APIView):
    """Get workflow visualization data (Mermaid diagrams)."""

    def get(self, request):
        workflow_type = request.query_params.get("type", "recursive_qa")

        if workflow_type == "recursive_qa":
            engine = _get_workflow_engine()
            if engine:
                mermaid = engine.get_mermaid_diagram()
            else:
                from .services.langgraph_workflow import RecursiveQAWorkflow
                mermaid = RecursiveQAWorkflow._get_default_mermaid()
        elif workflow_type == "multi_agent":
            orchestrator = _get_multi_agent_orchestrator()
            if orchestrator:
                mermaid = orchestrator.get_mermaid_diagram()
            else:
                mermaid = ""
        else:
            mermaid = ""

        return Response({
            "workflow_type": workflow_type,
            "mermaid_diagram": mermaid,
        })


class MCPView(APIView):
    """MCP (Model Context Protocol) endpoints."""

    def get(self, request):
        """List MCP tools and server info."""
        mcp = _get_mcp_server()
        action = request.query_params.get("action", "info")

        if action == "tools":
            return Response({"tools": mcp.list_tools()})
        elif action == "resources":
            return Response({"resources": mcp.list_resources()})
        else:
            return Response(mcp.get_server_info())

    def post(self, request):
        """Call an MCP tool."""
        serializer = MCPToolCallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mcp = _get_mcp_server()
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                mcp.call_tool(
                    serializer.validated_data["tool_name"],
                    serializer.validated_data["arguments"],
                )
            )
        finally:
            loop.close()

        return Response(result)


class A2AView(APIView):
    """A2A (Agent-to-Agent) protocol endpoints."""

    def get(self, request):
        """Discover agents and protocol info."""
        handler = _get_a2a_handler()
        action = request.query_params.get("action", "info")

        if action == "discover":
            capability = request.query_params.get("capability")
            return Response({"agents": handler.discover_agents(capability)})
        elif action == "messages":
            limit = int(request.query_params.get("limit", 50))
            return Response({"messages": handler.get_message_log(limit)})
        else:
            return Response(handler.get_protocol_info())

    def post(self, request):
        """Send an A2A task."""
        handler = _get_a2a_handler()
        action = request.data.get("action", "send_task")

        if action == "send_task":
            result = handler.send_task(
                sender_id=request.data.get("sender_id", ""),
                receiver_id=request.data.get("receiver_id", ""),
                task_type=request.data.get("task_type", ""),
                payload=request.data.get("payload", {}),
            )
            return Response(result)
        elif action == "complete_task":
            result = handler.complete_task(
                task_id=request.data.get("task_id", ""),
                result=request.data.get("result", {}),
            )
            return Response(result)
        else:
            return Response(
                {"error": f"Unknown action: {action}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
