"""Agents app configuration and singleton service management."""
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

# Module-level singletons
_workflow_engine = None
_multi_agent_orchestrator = None
_mcp_server = None
_a2a_handler = None
_vectorstore = None


def get_vectorstore():
    """Get or create the shared ChromaDB vectorstore."""
    global _vectorstore
    if _vectorstore is None:
        try:
            from django.conf import settings
            import chromadb
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings

            chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=int(settings.CHROMA_PORT),
            )

            embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=settings.OPENAI_BASE_URL,
            )

            _vectorstore = Chroma(
                client=chroma_client,
                collection_name="Research_Papers",
                embedding_function=embeddings,
            )
            logger.info("ChromaDB vectorstore initialized")
        except Exception as e:
            logger.warning(f"Could not initialize vectorstore: {e}")
    return _vectorstore


def get_workflow_engine():
    """Get or create the RecursiveQAWorkflow singleton."""
    global _workflow_engine
    if _workflow_engine is None:
        try:
            from .services.langgraph_workflow import RecursiveQAWorkflow
            vs = get_vectorstore()
            if vs is None:
                return None
            _workflow_engine = RecursiveQAWorkflow()
            _workflow_engine.initialize_retriever(vs)
            logger.info("RecursiveQAWorkflow engine initialized")
        except Exception as e:
            logger.warning(f"Could not initialize workflow engine: {e}")
    return _workflow_engine


def get_multi_agent_orchestrator():
    """Get or create the MultiAgentOrchestrator singleton."""
    global _multi_agent_orchestrator
    if _multi_agent_orchestrator is None:
        try:
            from .services.multi_agent_orchestrator import MultiAgentOrchestrator
            from langchain.tools.retriever import create_retriever_tool

            vs = get_vectorstore()
            retriever_tool = None
            if vs:
                retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 3})
                retriever_tool = create_retriever_tool(
                    retriever,
                    "retrieve_research_papers",
                    "Search and return information from indexed research papers.",
                )

            _multi_agent_orchestrator = MultiAgentOrchestrator(retriever_tool=retriever_tool)
            logger.info("MultiAgentOrchestrator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize multi-agent orchestrator: {e}")
    return _multi_agent_orchestrator


def get_mcp_server():
    """Get or create the MCP server singleton."""
    global _mcp_server
    if _mcp_server is None:
        from .services.mcp_server import MCPToolServer
        _mcp_server = MCPToolServer()
        logger.info("MCP server initialized")
    return _mcp_server


def get_a2a_handler():
    """Get or create the A2A protocol handler singleton."""
    global _a2a_handler
    if _a2a_handler is None:
        from .services.a2a_protocol import A2AProtocolHandler
        _a2a_handler = A2AProtocolHandler()
        logger.info("A2A protocol handler initialized")
    return _a2a_handler


class AgentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agents"

    def ready(self):
        from .services.observability import ObservabilityManager
        ObservabilityManager.setup_langsmith()
        logger.info("Agents app ready — observability configured")
