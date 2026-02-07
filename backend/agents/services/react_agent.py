"""ReAct Research Agent - Adaptive reasoning and acting agent."""
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from django.conf import settings

logger = logging.getLogger(__name__)

REACT_SYSTEM_PROMPT = """You are an expert research assistant specialized in analyzing scientific papers and research documents.
You have access to a retrieval tool that can search through indexed research papers.

Your capabilities:
1. Analyze user questions and decide whether to retrieve information or respond directly
2. Use the retrieval tool to find relevant research paper content
3. Synthesize information from multiple retrieved documents
4. Provide accurate, well-cited answers based on the retrieved context

When a question requires research paper content, use the retrieval tool.
When a question is a simple greeting or doesn't require paper content, respond directly.

Always be thorough but concise in your responses."""


class ReActResearchAgent:
    """ReAct agent that decides between direct response and tool-based retrieval."""

    def __init__(self, retriever_tool=None, model_name: str = None):
        self.model_name = model_name or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0,
            max_tokens=500,
            top_p=0.95,
            frequency_penalty=1.2,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )
        self.retriever_tool = retriever_tool
        if retriever_tool:
            self.llm_with_tools = self.llm.bind_tools([retriever_tool])
        else:
            self.llm_with_tools = self.llm

    def generate_query_or_respond(self, messages: list) -> dict:
        """Decide whether to use tools (RAG) or respond directly."""
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_retrieve(self, response) -> bool:
        """Check if the model decided to use a tool."""
        return bool(response.tool_calls)
