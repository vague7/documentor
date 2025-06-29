from app.config import logger, get_settings
from app.vector.chroma_client import get_vectorstore
from app.models.schemas import ChatResponse

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Shared history store
from app.history_store import DEFAULT_HISTORY_STORE


def _build_prompt_template() -> ChatPromptTemplate:
    """Return a chat prompt template compatible with create_stuff_documents_chain."""
    # Reuse same wording as earlier PromptTemplate but as ChatPrompt with roles
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an API documentation assistant. Use the provided context to answer the question.\n\n{context}",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )


def answer_query(user_question: str, session_id: str = "default") -> ChatResponse:
    """
    Retrieve relevant document chunks from ChromaDB Cloud and answer the user's question
    using Gemini via LangChain.
    """
    try:
        # RAG chain with conversational memory
        rag_chain = _build_rag_with_memory()

        result = rag_chain.invoke(
            {"input": user_question},
            config={"configurable": {"session_id": session_id}},
        )

        answer_text: str = result["answer"]
        context_docs = result.get("context", [])  # list of Documents
        sources = [doc.page_content for doc in context_docs] if context_docs else None

        logger.info("Query answered. Length of answer: %d", len(answer_text))
        return ChatResponse(answer=answer_text, sources=sources)

    except Exception as e:
        logger.error("Failed to answer query: %s", e)
        return ChatResponse(
            answer="Sorry, an error occurred while processing your question.",
            sources=None,
        )


# ---------------------------------------------------------------------------
# RAG chain builder (Runnable graph)
# ---------------------------------------------------------------------------


def _build_base_rag_chain():
    """Return a configured RunnableSequence for RAG QA."""
    settings = get_settings()

    retriever = get_vectorstore().as_retriever()
    qa_prompt = _build_prompt_template()
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.gemini_api_key)

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def _build_rag_with_memory() -> RunnableWithMessageHistory:
    """Return a RAG chain wrapped with conversational memory."""
    base_chain = _build_base_rag_chain()
    return RunnableWithMessageHistory(
        base_chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )


# ---------------------------------------------------------------------------
# Streaming & async helpers
# ---------------------------------------------------------------------------


def stream_answer(user_question: str, session_id: str = "default"):
    """Yield answer chunks as they stream from the model."""
    rag_chain = _build_rag_with_memory()
    for chunk in rag_chain.stream(
        {"input": user_question},
        config={"configurable": {"session_id": session_id}},
    ):
        yield chunk


async def answer_query_async(user_question: str, session_id: str = "default") -> ChatResponse:
    """Async version of answer_query using `.ainvoke()`."""
    rag_chain = _build_rag_with_memory()
    try:
        result = await rag_chain.ainvoke(
            {"input": user_question},
            config={"configurable": {"session_id": session_id}},
        )
        answer_text: str = result["answer"]
        context_docs = result.get("context", [])
        sources = [doc.page_content for doc in context_docs] if context_docs else None
        return ChatResponse(answer=answer_text, sources=sources)
    except Exception as e:
        logger.error("Async query failed: %s", e)
        return ChatResponse(answer="Error", sources=None)


def _get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Return a ChatMessageHistory for *session_id* using the shared store."""
    return DEFAULT_HISTORY_STORE.get(session_id) 