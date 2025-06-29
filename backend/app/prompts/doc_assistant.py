"""Prompt templates for the documentation assistant use-case."""

from langchain_core.prompts import PromptTemplate

DOC_ASSISTANT_PROMPT = PromptTemplate.from_template(
    """You are an API documentation assistant. Use the provided context to answer the question.
Context:
{context}

Question: {question}
Answer:"""
)

__all__ = ["DOC_ASSISTANT_PROMPT"] 