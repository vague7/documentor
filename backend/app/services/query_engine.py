from typing import List
import logging
from app.config import logger, get_settings
from app.vector.chroma_client import query_similar_docs
from app.models.schemas import ChatResponse

from langchain_google_genai import ChatGoogleGenerativeAI


def _build_prompt(context_chunks: List[str], question: str) -> str:
    """Build a prompt for Gemini given context chunks and the user question."""
    context = "\n".join(context_chunks)
    prompt = (
        "You are an API documentation assistant. Use the provided context to answer the question.\n"  # noqa: E501
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )
    return prompt


def answer_query(user_question: str) -> ChatResponse:
    """
    Retrieve relevant document chunks from ChromaDB Cloud and answer the user's question
    using Gemini via LangChain.
    """
    try:
        settings = get_settings()

        # Retrieve relevant chunks
        relevant_chunks = query_similar_docs(user_question)

        # Build prompt
        prompt = _build_prompt(relevant_chunks, user_question)

        # Initialize Gemini chat model
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.gemini_api_key)

        # Get answer (predict returns str)
        answer_text: str = llm.predict(prompt)

        logger.info("Query answered. Length of answer: %d", len(answer_text))
        return ChatResponse(answer=answer_text, sources=relevant_chunks)

    except Exception as e:
        logger.error("Failed to answer query: %s", e)
        return ChatResponse(
            answer="Sorry, an error occurred while processing your question.",
            sources=None,
        ) 