"""Document grading service - evaluates relevance of retrieved documents."""
import logging
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from django.conf import settings

logger = logging.getLogger(__name__)

GRADE_PROMPT = (
    "You are evaluating whether a retrieved document is relevant to a user question.\n\n"
    "Document:\n{context}\n\n"
    "Question:\n{question}\n\n"
    "Consider relevance in terms of concepts and topics that naturally relate to "
    "the subject matter of the question. "
    "Give a clear 'yes' if the document meaningfully relates to or could help "
    "answer the question, even partially. "
    "Give a 'no' only if the document is entirely unrelated or irrelevant to the question.\n\n"
    "Respond with a binary score: 'yes' or 'no'."
)


class GradeDocuments(BaseModel):
    """Binary score for document relevance check."""

    binary_score: Literal["yes", "no"] = Field(
        description="Relevance score: 'yes' if relevant, 'no' if not"
    )


class DocumentGrader:
    """Grades retrieved documents for relevance to a query."""

    def __init__(self, model_name: str = None, temperature: float = 0.0):
        self.model_name = model_name or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )
        self.structured_llm = self.llm.with_structured_output(GradeDocuments)
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", GRADE_PROMPT)]
        )
        self.chain = self.prompt | self.structured_llm

    def grade(self, question: str, document_content: str) -> str:
        """Grade a single document's relevance to the question.

        Returns 'yes' or 'no'.
        """
        try:
            result = self.chain.invoke({
                "context": document_content,
                "question": question,
            })
            return result.binary_score
        except Exception as e:
            logger.error(f"Error grading document: {e}")
            return "no"

    def grade_documents(self, question: str, documents: list) -> tuple[list, list]:
        """Grade a list of documents, returning relevant and irrelevant lists."""
        relevant = []
        irrelevant = []

        for doc in documents:
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)
            score = self.grade(question, content)
            if score == "yes":
                relevant.append(doc)
            else:
                irrelevant.append(doc)

        logger.info(
            f"Graded {len(documents)} docs: {len(relevant)} relevant, "
            f"{len(irrelevant)} irrelevant"
        )
        return relevant, irrelevant
