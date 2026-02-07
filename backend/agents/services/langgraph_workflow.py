"""
LangGraph Recursive QA Workflow — core workflow engine.

Implements the full Adaptive ReAct workflow from the notebook:
  1. generate_query_or_respond — decides to answer directly or retrieve
  2. retrieve (ToolNode) — fetches relevant chunks from vector store
  3. grade_documents — evaluates relevance of retrieved documents
  4. rewrite_question — refines unclear or off-topic queries
  5. generate_answer — produces final answer from context
"""
import logging
import time
import uuid
from typing import Literal, Optional

from django.conf import settings
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from .document_grader import DocumentGrader
from .query_rewriter import QueryRewriter
from .observability import ObservabilityManager

logger = logging.getLogger(__name__)

GENERATE_PROMPT = """You are an assistant whose task is to review the provided context and answer the user's question.
Answer the question based only on this context and do not mention the context itself.
If the answer is not found in the context, respond "I don't know".
Keep your answer concise, using a maximum of three sentences.

Question: {question}
Context: {context}
"""


class RecursiveQAWorkflow:
    """LangGraph-based recursive QA workflow with adaptive ReAct pattern."""

    def __init__(
        self,
        collection_name: str = "Research_Papers",
        max_iterations: int = 5,
    ):
        self.collection_name = collection_name
        self.max_iterations = max_iterations

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            max_tokens=500,
            top_p=0.95,
            frequency_penalty=1.2,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )

        # Sub-components
        self.grader = DocumentGrader()
        self.rewriter = QueryRewriter()

        # Execution tracing
        self._current_trace = []

        # Build workflow
        self.retriever_tool = None
        self.graph = None

    def initialize_retriever(self, vectorstore):
        """Initialize retriever from a vector store."""
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3},
        )
        self.retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_research_papers",
            "Search and return information from indexed research papers. "
            "Contains detailed research outcomes on Agentic AI and related topics.",
        )
        self._build_graph()

    def _build_graph(self):
        """Build the LangGraph StateGraph workflow."""
        workflow = StateGraph(MessagesState)

        # Define nodes
        workflow.add_node("generate_query_or_respond", self._generate_query_or_respond)
        workflow.add_node("retrieve", ToolNode([self.retriever_tool]))
        workflow.add_node("rewrite_question", self._rewrite_question)
        workflow.add_node("generate_answer", self._generate_answer)

        # Define edges
        workflow.add_edge(START, "generate_query_or_respond")
        workflow.add_conditional_edges(
            "generate_query_or_respond",
            tools_condition,
            {"tools": "retrieve", END: END},
        )
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_documents,
            {"generate_answer": "generate_answer", "rewrite_question": "rewrite_question"},
        )
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("rewrite_question", "generate_query_or_respond")

        self.graph = workflow.compile()
        logger.info("LangGraph workflow compiled successfully")

    def _generate_query_or_respond(self, state: MessagesState):
        """Node 1: Decide whether to use tools (RAG) or respond directly."""
        self._trace_node("generate_query_or_respond", "Deciding: retrieve or respond")
        response = self.llm.bind_tools([self.retriever_tool]).invoke(state["messages"])
        return {"messages": [response]}

    def _grade_documents(self, state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
        """Conditional edge: Grade retrieved documents for relevance."""
        self._trace_node("grade_documents", "Evaluating document relevance")
        messages = state["messages"]

        # Find the last user question
        question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                question = msg.content
                break

        # Find the last tool message (retrieved content)
        tool_content = ""
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                tool_content = msg.content
                break

        if not tool_content:
            self._trace_node("grade_documents", "No content retrieved -> rewrite")
            return "rewrite_question"

        score = self.grader.grade(question, tool_content)
        if score == "yes":
            self._trace_node("grade_documents", f"Relevant (score={score}) -> generate")
            return "generate_answer"
        else:
            self._trace_node("grade_documents", f"Not relevant (score={score}) -> rewrite")
            return "rewrite_question"

    def _rewrite_question(self, state: MessagesState):
        """Node 2: Rewrite the question for better retrieval."""
        self._trace_node("rewrite_question", "Rewriting query for better results")
        messages = state["messages"]

        # Find the last user question
        question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                question = msg.content
                break

        rewritten = self.rewriter.rewrite(question)
        return {"messages": [HumanMessage(content=rewritten)]}

    def _generate_answer(self, state: MessagesState):
        """Node 3: Generate the final answer from retrieved context."""
        self._trace_node("generate_answer", "Generating final answer from context")
        messages = state["messages"]

        # Find question and context
        question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                question = msg.content
                break

        context = ""
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                context = msg.content
                break

        prompt = ChatPromptTemplate.from_messages([("system", GENERATE_PROMPT)])
        chain = prompt | self.llm
        response = chain.invoke({"question": question, "context": context})
        return {"messages": [response]}

    def _trace_node(self, node_name: str, detail: str):
        """Record a node execution in the trace."""
        self._current_trace.append({
            "node": node_name,
            "detail": detail,
            "timestamp": time.time(),
        })

    async def execute(self, query: str, session_id: str = None) -> dict:
        """Execute the workflow with a user query."""
        if self.graph is None:
            raise RuntimeError("Workflow not initialized. Call initialize_retriever first.")

        self._current_trace = []
        start_time = time.time()

        # Set up observability
        callbacks = []
        langfuse_handler = ObservabilityManager.get_langfuse_callback_handler()
        if langfuse_handler:
            callbacks.append(langfuse_handler)

        trace = ObservabilityManager.create_trace(
            name="recursive_qa_workflow",
            session_id=session_id,
            metadata={"query": query},
        )

        try:
            input_data = {
                "messages": [HumanMessage(content=query)],
            }

            config = {}
            if callbacks:
                config["callbacks"] = callbacks

            # Execute graph with recursion limit to prevent infinite loops
            result = self.graph.invoke(
                input_data,
                config={"recursion_limit": self.max_iterations * 3, **config},
            )

            # Extract final answer
            final_message = result["messages"][-1]
            answer = final_message.content if hasattr(final_message, "content") else str(final_message)

            duration_ms = int((time.time() - start_time) * 1000)

            # Log score to Langfuse
            if trace:
                ObservabilityManager.log_score(
                    trace_id=str(trace.id) if hasattr(trace, "id") else "",
                    name="workflow_completed",
                    value=1.0,
                    comment=f"Completed in {duration_ms}ms",
                )

            return {
                "answer": answer,
                "trace": self._current_trace,
                "duration_ms": duration_ms,
                "messages": [
                    {
                        "role": "ai" if isinstance(m, AIMessage) else
                               "human" if isinstance(m, HumanMessage) else
                               "tool" if isinstance(m, ToolMessage) else "unknown",
                        "content": m.content if hasattr(m, "content") else str(m),
                        "tool_calls": getattr(m, "tool_calls", None),
                    }
                    for m in result["messages"]
                ],
                "langfuse_trace_id": str(trace.id) if trace and hasattr(trace, "id") else "",
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            if trace:
                ObservabilityManager.log_score(
                    trace_id=str(trace.id) if hasattr(trace, "id") else "",
                    name="workflow_error",
                    value=0.0,
                    comment=str(e),
                )
            raise

    def execute_sync(self, query: str, session_id: str = None) -> dict:
        """Synchronous wrapper for workflow execution."""
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.execute(query, session_id))
        finally:
            loop.close()

    def get_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram of the workflow graph."""
        if self.graph is None:
            return self._get_default_mermaid()
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception:
            return self._get_default_mermaid()

    def get_graph_png(self) -> Optional[bytes]:
        """Generate PNG visualization of the workflow graph."""
        if self.graph is None:
            return None
        try:
            return self.graph.get_graph().draw_mermaid_png()
        except Exception as e:
            logger.warning(f"Could not generate graph PNG: {e}")
            return None

    @staticmethod
    def _get_default_mermaid() -> str:
        return """graph TD
    __start__([Start]) --> generate_query_or_respond
    generate_query_or_respond -->|uses tools| retrieve
    generate_query_or_respond -->|direct answer| __end__([End])
    retrieve --> grade_documents{Grade Documents}
    grade_documents -->|relevant| generate_answer
    grade_documents -->|not relevant| rewrite_question
    rewrite_question --> generate_query_or_respond
    generate_answer --> __end__([End])

    style __start__ fill:#4CAF50,color:#fff
    style __end__ fill:#f44336,color:#fff
    style generate_query_or_respond fill:#2196F3,color:#fff
    style retrieve fill:#FF9800,color:#fff
    style grade_documents fill:#9C27B0,color:#fff
    style rewrite_question fill:#FF5722,color:#fff
    style generate_answer fill:#00BCD4,color:#fff"""
