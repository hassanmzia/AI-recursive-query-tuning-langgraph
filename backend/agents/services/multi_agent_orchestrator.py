"""
Multi-Agent Orchestrator — coordinates multiple specialized agents.

Agents:
  - Research Agent: Handles document retrieval and analysis
  - QA Specialist: Answers questions using retrieved context
  - Critique Agent: Evaluates answer quality and suggests improvements
  - Summarization Agent: Condenses information from multiple sources
  - Query Rewriter: Refines queries for better results
"""
import logging
import time
import uuid
from typing import TypedDict, Annotated, Literal, Optional

from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from .observability import ObservabilityManager

logger = logging.getLogger(__name__)


# --- Agent Prompts ---

RESEARCH_AGENT_PROMPT = """You are a Research Agent specialized in analyzing scientific papers.
Your role: Search, retrieve, and compile relevant information from research papers.
Provide detailed findings with specific references to papers when possible.
Focus on accuracy and comprehensiveness.

Question: {question}
Retrieved Context: {context}

Provide your research findings:"""

QA_SPECIALIST_PROMPT = """You are a QA Specialist Agent.
Your role: Synthesize research findings into clear, accurate answers.
Use the research context to formulate a comprehensive response.
If the context doesn't contain enough information, clearly state what is missing.

Question: {question}
Research Findings: {research_findings}

Provide your answer:"""

CRITIQUE_AGENT_PROMPT = """You are a Critique Agent that evaluates the quality of answers.
Analyze the answer for:
1. Accuracy — Does it correctly represent the source material?
2. Completeness — Does it fully address the question?
3. Clarity — Is it well-structured and easy to understand?
4. Evidence — Is it supported by the retrieved context?

Question: {question}
Answer: {answer}
Original Context: {context}

Provide a quality score (1-10) and specific feedback.
Format: SCORE: X/10
FEEDBACK: <your feedback>
NEEDS_REVISION: <yes/no>"""

SUMMARIZER_PROMPT = """You are a Summarization Agent.
Your role: Create concise, informative summaries that capture the essential points.
Maintain accuracy while reducing verbosity.

Content to summarize: {content}
Focus area: {focus}

Provide a concise summary (3-5 sentences):"""


class MultiAgentState(TypedDict):
    """State shared across agents in the multi-agent workflow."""
    question: str
    context: str
    research_findings: str
    qa_answer: str
    critique_score: int
    critique_feedback: str
    needs_revision: bool
    final_answer: str
    summary: str
    iteration: int
    max_iterations: int
    agent_trace: list


class CritiqueResult(BaseModel):
    """Structured output from the critique agent."""
    score: int = Field(ge=1, le=10, description="Quality score 1-10")
    feedback: str = Field(description="Specific feedback")
    needs_revision: bool = Field(description="Whether the answer needs revision")


class MultiAgentOrchestrator:
    """Orchestrates multiple agents through a LangGraph workflow."""

    def __init__(self, retriever_tool=None):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            max_tokens=800,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )
        self.retriever_tool = retriever_tool
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the multi-agent orchestration graph."""
        workflow = StateGraph(MultiAgentState)

        # Add nodes
        workflow.add_node("research_agent", self._research_agent)
        workflow.add_node("qa_specialist", self._qa_specialist)
        workflow.add_node("critique_agent", self._critique_agent)
        workflow.add_node("revision_agent", self._revision_agent)
        workflow.add_node("summarizer", self._summarizer)

        # Define flow
        workflow.add_edge(START, "research_agent")
        workflow.add_edge("research_agent", "qa_specialist")
        workflow.add_edge("qa_specialist", "critique_agent")
        workflow.add_conditional_edges(
            "critique_agent",
            self._should_revise,
            {"revise": "revision_agent", "accept": "summarizer"},
        )
        workflow.add_edge("revision_agent", "critique_agent")
        workflow.add_edge("summarizer", END)

        return workflow.compile()

    def _research_agent(self, state: MultiAgentState) -> dict:
        """Research Agent: Retrieve and analyze relevant documents."""
        question = state["question"]
        context = state.get("context", "")
        trace = state.get("agent_trace", [])

        # If we have a retriever, use it
        if self.retriever_tool and not context:
            try:
                context = self.retriever_tool.invoke({"query": question})
            except Exception as e:
                logger.warning(f"Retriever failed: {e}")
                context = ""

        prompt = ChatPromptTemplate.from_messages([("system", RESEARCH_AGENT_PROMPT)])
        chain = prompt | self.llm
        result = chain.invoke({"question": question, "context": context})

        trace.append({
            "agent": "research_agent",
            "action": "analyze",
            "timestamp": time.time(),
        })

        return {
            "research_findings": result.content,
            "context": context,
            "agent_trace": trace,
        }

    def _qa_specialist(self, state: MultiAgentState) -> dict:
        """QA Specialist: Synthesize findings into an answer."""
        prompt = ChatPromptTemplate.from_messages([("system", QA_SPECIALIST_PROMPT)])
        chain = prompt | self.llm
        result = chain.invoke({
            "question": state["question"],
            "research_findings": state.get("research_findings", ""),
        })

        trace = state.get("agent_trace", [])
        trace.append({
            "agent": "qa_specialist",
            "action": "answer",
            "timestamp": time.time(),
        })

        return {
            "qa_answer": result.content,
            "agent_trace": trace,
        }

    def _critique_agent(self, state: MultiAgentState) -> dict:
        """Critique Agent: Evaluate answer quality."""
        prompt = ChatPromptTemplate.from_messages([("system", CRITIQUE_AGENT_PROMPT)])
        chain = prompt | self.llm
        result = chain.invoke({
            "question": state["question"],
            "answer": state.get("qa_answer", ""),
            "context": state.get("context", ""),
        })

        content = result.content
        score = 7
        needs_revision = False
        feedback = content

        # Parse structured response
        for line in content.split("\n"):
            line_stripped = line.strip()
            if line_stripped.startswith("SCORE:"):
                try:
                    score = int(line_stripped.split("/")[0].split(":")[-1].strip())
                except (ValueError, IndexError):
                    pass
            elif line_stripped.startswith("NEEDS_REVISION:"):
                needs_revision = "yes" in line_stripped.lower()
            elif line_stripped.startswith("FEEDBACK:"):
                feedback = line_stripped.split(":", 1)[-1].strip()

        iteration = state.get("iteration", 0) + 1
        max_iter = state.get("max_iterations", 3)
        if iteration >= max_iter:
            needs_revision = False

        trace = state.get("agent_trace", [])
        trace.append({
            "agent": "critique_agent",
            "action": "evaluate",
            "score": score,
            "needs_revision": needs_revision,
            "iteration": iteration,
            "timestamp": time.time(),
        })

        return {
            "critique_score": score,
            "critique_feedback": feedback,
            "needs_revision": needs_revision,
            "iteration": iteration,
            "agent_trace": trace,
        }

    def _should_revise(self, state: MultiAgentState) -> Literal["revise", "accept"]:
        """Decide whether to revise the answer based on critique."""
        if state.get("needs_revision", False):
            return "revise"
        return "accept"

    def _revision_agent(self, state: MultiAgentState) -> dict:
        """Revision Agent: Improve the answer based on critique feedback."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Revision Agent. Improve the following answer based on "
                "the critique feedback. Maintain accuracy and improve clarity.\n\n"
                "Original Question: {question}\n"
                "Current Answer: {answer}\n"
                "Critique Feedback: {feedback}\n"
                "Context: {context}\n\n"
                "Provide an improved answer:"
            ))
        ])
        chain = prompt | self.llm
        result = chain.invoke({
            "question": state["question"],
            "answer": state.get("qa_answer", ""),
            "feedback": state.get("critique_feedback", ""),
            "context": state.get("context", ""),
        })

        trace = state.get("agent_trace", [])
        trace.append({
            "agent": "revision_agent",
            "action": "revise",
            "timestamp": time.time(),
        })

        return {
            "qa_answer": result.content,
            "agent_trace": trace,
        }

    def _summarizer(self, state: MultiAgentState) -> dict:
        """Summarizer: Create a concise final summary."""
        prompt = ChatPromptTemplate.from_messages([("system", SUMMARIZER_PROMPT)])
        chain = prompt | self.llm
        result = chain.invoke({
            "content": state.get("qa_answer", ""),
            "focus": state["question"],
        })

        trace = state.get("agent_trace", [])
        trace.append({
            "agent": "summarizer",
            "action": "summarize",
            "timestamp": time.time(),
        })

        return {
            "final_answer": state.get("qa_answer", ""),
            "summary": result.content,
            "agent_trace": trace,
        }

    def execute(self, question: str, context: str = "") -> dict:
        """Execute the multi-agent workflow."""
        start_time = time.time()

        initial_state: MultiAgentState = {
            "question": question,
            "context": context,
            "research_findings": "",
            "qa_answer": "",
            "critique_score": 0,
            "critique_feedback": "",
            "needs_revision": False,
            "final_answer": "",
            "summary": "",
            "iteration": 0,
            "max_iterations": 3,
            "agent_trace": [],
        }

        result = self.graph.invoke(initial_state)
        duration_ms = int((time.time() - start_time) * 1000)

        return {
            "answer": result.get("final_answer", ""),
            "summary": result.get("summary", ""),
            "critique_score": result.get("critique_score", 0),
            "critique_feedback": result.get("critique_feedback", ""),
            "iterations": result.get("iteration", 0),
            "agent_trace": result.get("agent_trace", []),
            "duration_ms": duration_ms,
        }

    def get_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram for multi-agent workflow."""
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception:
            return """graph TD
    __start__([Start]) --> research_agent
    research_agent[Research Agent] --> qa_specialist[QA Specialist]
    qa_specialist --> critique_agent[Critique Agent]
    critique_agent -->|needs revision| revision_agent[Revision Agent]
    critique_agent -->|accepted| summarizer[Summarizer]
    revision_agent --> critique_agent
    summarizer --> __end__([End])

    style __start__ fill:#4CAF50,color:#000
    style __end__ fill:#f44336,color:#000
    style research_agent fill:#2196F3,color:#000
    style qa_specialist fill:#FF9800,color:#000
    style critique_agent fill:#9C27B0,color:#000
    style revision_agent fill:#FF5722,color:#000
    style summarizer fill:#00BCD4,color:#000"""
