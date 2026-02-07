"""
A2A (Agent-to-Agent) Protocol Handler.

Implements inter-agent communication following the A2A protocol specification.
Enables agents to discover each other, send tasks, and exchange messages.
"""
import logging
import uuid
import time
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class AgentCard:
    """Represents an agent's capabilities and contact information (A2A Agent Card)."""

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: list[str],
        endpoint: str,
        agent_type: str = "general",
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.endpoint = endpoint
        self.agent_type = agent_type

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "agentType": self.agent_type,
            "protocolVersion": settings.A2A_PROTOCOL_VERSION,
        }


class A2ATask:
    """Represents a task in the A2A protocol."""

    def __init__(
        self,
        task_type: str,
        payload: dict,
        sender: str,
        receiver: str,
    ):
        self.id = str(uuid.uuid4())
        self.task_type = task_type
        self.payload = payload
        self.sender = sender
        self.receiver = receiver
        self.status = "pending"
        self.result = None
        self.created_at = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "taskType": self.task_type,
            "payload": self.payload,
            "sender": self.sender,
            "receiver": self.receiver,
            "status": self.status,
            "result": self.result,
            "createdAt": self.created_at,
        }


class A2AProtocolHandler:
    """Handles Agent-to-Agent protocol communication."""

    def __init__(self):
        self.registry: dict[str, AgentCard] = {}
        self.pending_tasks: dict[str, A2ATask] = {}
        self.message_log: list[dict] = []
        self._register_default_agents()

    def _register_default_agents(self):
        """Register the default agents in the system."""
        agents = [
            AgentCard(
                name="Research Agent",
                description="Specialized in searching and analyzing research papers",
                capabilities=["search", "analyze", "retrieve"],
                endpoint="/api/agents/research/",
                agent_type="react_researcher",
            ),
            AgentCard(
                name="QA Specialist",
                description="Synthesizes research findings into clear answers",
                capabilities=["answer", "synthesize", "explain"],
                endpoint="/api/agents/qa/",
                agent_type="qa_specialist",
            ),
            AgentCard(
                name="Critique Agent",
                description="Evaluates answer quality and provides feedback",
                capabilities=["evaluate", "critique", "score"],
                endpoint="/api/agents/critique/",
                agent_type="critique",
            ),
            AgentCard(
                name="Summarizer",
                description="Creates concise summaries of content",
                capabilities=["summarize", "condense", "abstract"],
                endpoint="/api/agents/summarize/",
                agent_type="summarizer",
            ),
            AgentCard(
                name="Query Rewriter",
                description="Refines and improves user queries",
                capabilities=["rewrite", "refine", "clarify"],
                endpoint="/api/agents/rewrite/",
                agent_type="query_rewriter",
            ),
            AgentCard(
                name="Orchestrator",
                description="Coordinates multi-agent workflows",
                capabilities=["orchestrate", "delegate", "coordinate"],
                endpoint="/api/agents/orchestrate/",
                agent_type="orchestrator",
            ),
        ]
        for agent in agents:
            self.register_agent(agent)

    def register_agent(self, agent_card: AgentCard):
        """Register an agent in the A2A registry."""
        self.registry[agent_card.id] = agent_card
        logger.info(f"A2A agent registered: {agent_card.name} ({agent_card.id})")

    def discover_agents(self, capability: str = None) -> list[dict]:
        """Discover registered agents, optionally filtered by capability."""
        agents = list(self.registry.values())
        if capability:
            agents = [a for a in agents if capability in a.capabilities]
        return [a.to_dict() for a in agents]

    def send_task(
        self,
        sender_id: str,
        receiver_id: str,
        task_type: str,
        payload: dict,
    ) -> dict:
        """Send a task from one agent to another."""
        sender = self.registry.get(sender_id)
        receiver = self.registry.get(receiver_id)

        if not sender or not receiver:
            return {"error": "Agent not found"}

        task = A2ATask(
            task_type=task_type,
            payload=payload,
            sender=sender.name,
            receiver=receiver.name,
        )
        self.pending_tasks[task.id] = task

        self.message_log.append({
            "type": "task_sent",
            "task_id": task.id,
            "sender": sender.name,
            "receiver": receiver.name,
            "task_type": task_type,
            "timestamp": time.time(),
        })

        logger.info(f"A2A task sent: {sender.name} -> {receiver.name} ({task_type})")
        return task.to_dict()

    def complete_task(self, task_id: str, result: dict) -> dict:
        """Mark a task as completed with a result."""
        task = self.pending_tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        task.status = "completed"
        task.result = result

        self.message_log.append({
            "type": "task_completed",
            "task_id": task.id,
            "timestamp": time.time(),
        })

        return task.to_dict()

    def get_task_status(self, task_id: str) -> dict:
        """Get the status of a task."""
        task = self.pending_tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        return task.to_dict()

    def get_message_log(self, limit: int = 50) -> list[dict]:
        """Get recent A2A messages."""
        return self.message_log[-limit:]

    def get_protocol_info(self) -> dict:
        """Get A2A protocol information."""
        return {
            "protocolVersion": settings.A2A_PROTOCOL_VERSION,
            "agents": len(self.registry),
            "pendingTasks": len([t for t in self.pending_tasks.values() if t.status == "pending"]),
            "completedTasks": len([t for t in self.pending_tasks.values() if t.status == "completed"]),
            "totalMessages": len(self.message_log),
        }
