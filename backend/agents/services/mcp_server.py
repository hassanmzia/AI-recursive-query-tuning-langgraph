"""
MCP (Model Context Protocol) Server — exposes tools and resources via MCP.

Provides standardized tool access for agents through the MCP protocol,
enabling external integrations and tool discovery.
"""
import logging
import json
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class MCPToolServer:
    """MCP-compatible tool server for the multi-agent system."""

    def __init__(self):
        self.tools = {}
        self.resources = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools available through MCP."""
        self.register_tool(
            name="retrieve_research_papers",
            description="Search and return information from indexed research papers",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for research papers",
                    }
                },
                "required": ["query"],
            },
            handler=self._handle_retrieve,
        )
        self.register_tool(
            name="grade_document",
            description="Evaluate whether a retrieved document is relevant to a question",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The user question"},
                    "document": {"type": "string", "description": "The document content"},
                },
                "required": ["question", "document"],
            },
            handler=self._handle_grade,
        )
        self.register_tool(
            name="rewrite_query",
            description="Rewrite a query for better research paper retrieval",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The original question"},
                },
                "required": ["question"],
            },
            handler=self._handle_rewrite,
        )
        self.register_tool(
            name="summarize_text",
            description="Summarize a piece of text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "max_sentences": {
                        "type": "integer",
                        "description": "Maximum number of sentences",
                        "default": 3,
                    },
                },
                "required": ["text"],
            },
            handler=self._handle_summarize,
        )
        self.register_tool(
            name="analyze_workflow",
            description="Analyze a workflow execution and provide insights",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "The workflow execution ID"},
                },
                "required": ["workflow_id"],
            },
            handler=self._handle_analyze_workflow,
        )

    def register_tool(self, name: str, description: str, input_schema: dict, handler=None):
        """Register a tool with the MCP server."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": handler,
        }
        logger.info(f"MCP tool registered: {name}")

    def register_resource(self, uri: str, name: str, description: str, mime_type: str = "text/plain"):
        """Register a resource with the MCP server."""
        self.resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
        }

    def list_tools(self) -> list:
        """List all available MCP tools."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for t in self.tools.values()
        ]

    def list_resources(self) -> list:
        """List all available MCP resources."""
        return list(self.resources.values())

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a registered MCP tool."""
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}

        tool = self.tools[name]
        handler = tool.get("handler")

        if handler is None:
            return {"error": f"Tool '{name}' has no handler"}

        try:
            result = handler(arguments)
            return {"content": [{"type": "text", "text": str(result)}]}
        except Exception as e:
            logger.error(f"MCP tool '{name}' execution failed: {e}")
            return {"error": str(e)}

    def get_server_info(self) -> dict:
        """Get MCP server information."""
        return {
            "name": "recursive-query-tuning-mcp",
            "version": "1.0.0",
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
            },
            "serverInfo": {
                "name": "Recursive Query Tuning MCP Server",
                "version": "1.0.0",
            },
        }

    # --- Tool Handlers ---

    def _handle_retrieve(self, args: dict) -> str:
        """Handle retrieve_research_papers tool call."""
        return f"Retrieval requested for: {args.get('query', '')}"

    def _handle_grade(self, args: dict) -> str:
        """Handle grade_document tool call."""
        from .document_grader import DocumentGrader
        grader = DocumentGrader()
        return grader.grade(args["question"], args["document"])

    def _handle_rewrite(self, args: dict) -> str:
        """Handle rewrite_query tool call."""
        from .query_rewriter import QueryRewriter
        rewriter = QueryRewriter()
        return rewriter.rewrite(args["question"])

    def _handle_summarize(self, args: dict) -> str:
        """Handle summarize_text tool call."""
        return f"Summary requested for text of length {len(args.get('text', ''))}"

    def _handle_analyze_workflow(self, args: dict) -> str:
        """Handle analyze_workflow tool call."""
        return f"Analysis requested for workflow: {args.get('workflow_id', '')}"
