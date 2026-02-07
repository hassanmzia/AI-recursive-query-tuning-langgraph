"""Query rewriting service - refines unclear or off-topic queries."""
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from django.conf import settings

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """You are an assistant that rewrites user questions to be more specific and focused for research paper retrieval.
If the question is vague, off-topic, or unclear, transform it into a clear, focused, and answerable question.
Preserve the user's original intent while making the question more precise.
Output only the rewritten question — no explanations, no extra words.

Original Question: {question}

Rewritten Question:"""


class QueryRewriter:
    """Rewrites and refines user queries for better retrieval."""

    def __init__(self, model_name: str = None, temperature: float = 0.0):
        self.model_name = model_name or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", REWRITE_PROMPT)]
        )
        self.chain = self.prompt | self.llm

    def rewrite(self, question: str) -> str:
        """Rewrite a question for better clarity and retrieval."""
        try:
            result = self.chain.invoke({"question": question})
            rewritten = result.content.strip()
            logger.info(f"Query rewritten: '{question}' -> '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return question
