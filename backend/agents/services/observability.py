"""Observability integration with LangSmith and Langfuse."""
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ObservabilityManager:
    """Manages LangSmith and Langfuse observability integrations."""

    _langfuse_instance = None

    @classmethod
    def get_langfuse(cls):
        """Get or create Langfuse client instance."""
        if cls._langfuse_instance is None:
            try:
                from langfuse import Langfuse

                cls._langfuse_instance = Langfuse(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST,
                )
                logger.info("Langfuse client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                cls._langfuse_instance = None
        return cls._langfuse_instance

    @classmethod
    def get_langfuse_callback_handler(cls):
        """Get Langfuse callback handler for LangChain."""
        try:
            from langfuse.callback import CallbackHandler

            return CallbackHandler(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
        except Exception as e:
            logger.warning(f"Failed to create Langfuse callback handler: {e}")
            return None

    @classmethod
    def create_trace(
        cls,
        name: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Create a new Langfuse trace."""
        langfuse = cls.get_langfuse()
        if langfuse is None:
            return None
        try:
            return langfuse.trace(
                name=name,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.warning(f"Failed to create Langfuse trace: {e}")
            return None

    @classmethod
    def log_score(
        cls,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ):
        """Log a score to Langfuse for evaluation."""
        langfuse = cls.get_langfuse()
        if langfuse is None:
            return
        try:
            langfuse.score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
        except Exception as e:
            logger.warning(f"Failed to log Langfuse score: {e}")

    @classmethod
    def setup_langsmith(cls):
        """Verify LangSmith configuration."""
        import os

        os.environ.setdefault("LANGCHAIN_TRACING_V2", settings.LANGCHAIN_TRACING_V2)
        if settings.LANGCHAIN_API_KEY:
            os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGCHAIN_API_KEY)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT)
        if settings.LANGCHAIN_API_KEY:
            logger.info(
                f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}"
            )
        else:
            logger.info("LangSmith API key not set - tracing disabled")
