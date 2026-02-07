"""WebSocket consumer for real-time workflow streaming."""
import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebSocketConsumer

logger = logging.getLogger(__name__)


class WorkflowStreamConsumer(AsyncWebSocketConsumer):
    """WebSocket consumer that streams workflow execution in real-time."""

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"].get("session_id", "default")
        self.group_name = f"workflow_{self.session_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "session_id": self.session_id,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages (query execution requests)."""
        try:
            data = json.loads(text_data)
            msg_type = data.get("type", "")

            if msg_type == "execute_query":
                await self.handle_query(data)
            elif msg_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON",
            }))

    async def handle_query(self, data):
        """Execute a query and stream results."""
        query = data.get("query", "")
        workflow_type = data.get("workflow_type", "recursive_qa")

        if not query:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Query is required",
            }))
            return

        await self.send(text_data=json.dumps({
            "type": "workflow_started",
            "query": query,
            "workflow_type": workflow_type,
        }))

        try:
            from .apps import get_workflow_engine, get_multi_agent_orchestrator

            if workflow_type == "recursive_qa":
                engine = get_workflow_engine()
                if engine is None:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Workflow engine not initialized",
                    }))
                    return

                # Stream node execution events
                await self.send(text_data=json.dumps({
                    "type": "node_executing",
                    "node": "generate_query_or_respond",
                    "detail": "Deciding whether to retrieve or respond directly",
                }))

                result = await engine.execute(query, session_id=self.session_id)

                # Send trace events
                for trace_item in result.get("trace", []):
                    await self.send(text_data=json.dumps({
                        "type": "node_executed",
                        "node": trace_item.get("node", ""),
                        "detail": trace_item.get("detail", ""),
                    }))

                await self.send(text_data=json.dumps({
                    "type": "workflow_completed",
                    "answer": result["answer"],
                    "duration_ms": result.get("duration_ms", 0),
                    "trace": result.get("trace", []),
                    "messages": result.get("messages", []),
                }))

            elif workflow_type == "multi_agent":
                orchestrator = get_multi_agent_orchestrator()
                if orchestrator is None:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Multi-agent orchestrator not initialized",
                    }))
                    return

                result = await asyncio.to_thread(orchestrator.execute, query)

                for trace_item in result.get("agent_trace", []):
                    await self.send(text_data=json.dumps({
                        "type": "agent_action",
                        "agent": trace_item.get("agent", ""),
                        "action": trace_item.get("action", ""),
                    }))

                await self.send(text_data=json.dumps({
                    "type": "workflow_completed",
                    "answer": result["answer"],
                    "summary": result.get("summary", ""),
                    "critique_score": result.get("critique_score", 0),
                    "duration_ms": result.get("duration_ms", 0),
                    "agent_trace": result.get("agent_trace", []),
                }))

        except Exception as e:
            logger.error(f"WebSocket workflow execution failed: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e),
            }))

    # Group message handlers
    async def workflow_update(self, event):
        """Handle workflow update messages from the channel layer."""
        await self.send(text_data=json.dumps(event["data"]))
