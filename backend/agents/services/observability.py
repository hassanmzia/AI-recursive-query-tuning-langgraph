"""Observability integration with LangSmith and Langfuse."""
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_PATTERNS = ("your-", "change-me", "placeholder", "xxx", "sk-lf-rqt-dev", "pk-lf-rqt-dev")


def _is_real_key(key: str) -> bool:
    """Return True only if the key looks like a real credential, not a placeholder."""
    if not key or not key.strip():
        return False
    lower = key.strip().lower()
    return not any(p in lower for p in _PLACEHOLDER_PATTERNS)


class ObservabilityManager:
    """Manages LangSmith and Langfuse observability integrations."""

    _langfuse_instance = None
    _callback_handler = None
    _langfuse_checked = False

    @classmethod
    def get_langfuse(cls):
        """Get or create Langfuse client instance."""
        if cls._langfuse_checked and cls._langfuse_instance is None:
            return None
        if cls._langfuse_instance is None:
            cls._langfuse_checked = True
            if not _is_real_key(settings.LANGFUSE_PUBLIC_KEY) or not _is_real_key(settings.LANGFUSE_SECRET_KEY):
                logger.info("Langfuse keys are placeholders — skipping Langfuse")
                return None
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
        """Get cached Langfuse callback handler for LangChain."""
        if cls._callback_handler is not None:
            return cls._callback_handler
        if not _is_real_key(settings.LANGFUSE_PUBLIC_KEY) or not _is_real_key(settings.LANGFUSE_SECRET_KEY):
            return None
        try:
            from langfuse.callback import CallbackHandler

            cls._callback_handler = CallbackHandler(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
            return cls._callback_handler
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
        """Configure LangSmith tracing — only if a real API key is provided."""
        import os

        api_key = settings.LANGCHAIN_API_KEY
        if _is_real_key(api_key):
            os.environ.setdefault("LANGCHAIN_TRACING_V2", settings.LANGCHAIN_TRACING_V2)
            os.environ.setdefault("LANGCHAIN_API_KEY", api_key)
            os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT)
            logger.info(
                f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}"
            )
        else:
            # Explicitly disable tracing when key is missing or placeholder
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            logger.info("LangSmith API key not set or placeholder — tracing disabled")
