from typing import Dict, Generator, Any, Sequence
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent  # type: ignore
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from app.config import get_settings, logger
from app.models.schemas import ChatResponse
from app.tools import TOOLS

# Shared history store
from app.history_store import DEFAULT_HISTORY_STORE

# ---------------------------------------------------------------------------
# Build agent (singleton)
# ---------------------------------------------------------------------------

_agent_executor = None


def _build_agent_executor():
    global _agent_executor
    if _agent_executor is not None:
        return _agent_executor

    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0,
        # Gemini doesn't understand a separate "system" role; this merges the
        # system prompt into the first user turn so the request is always valid.
        convert_system_message_to_human=True,
    )

    base_agent = create_react_agent(llm, TOOLS)
    # Wrap with message history so the agent is conversational
    _agent_executor = RunnableWithMessageHistory(
        base_agent,
        _get_session_history,
        input_messages_key="messages",
        history_messages_key="messages",  # re-use same key for past msgs
    )
    return _agent_executor


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serialise_message(m: BaseMessage) -> dict:
    """Convert LangChain message objects to a lightweight JSON-ish dict.
    Only used for debug logging so we don't leak user data in production logs.
    """
    return {
        "type": m.__class__.__name__,
        "content": getattr(m, "content", ""),
        # Additional attrs (e.g. tool_calls) are ignored for brevity.
    }


def _log_payload(session_id: str, outgoing: Sequence[BaseMessage]) -> None:
    """Log the full message list that will be sent to Gemini."""
    try:
        history = _get_session_history(session_id).messages
        logger.debug(">>> PAYLOAD >>> %s", json.dumps(
            [_serialise_message(m) for m in history + list(outgoing)], indent=2)
        )
    except Exception:  # never allow debug helpers to kill the request
        pass


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------


def run_agent_query(user_question: str, session_id: str = "default") -> ChatResponse:
    """Run the developer assistant agent with the given question."""
    if not user_question or not user_question.strip():
        logger.warning("Rejected empty user_question for /agent (session=%s)", session_id)
        return ChatResponse(answer="Question must not be empty.", sources=None)

    agent = _build_agent_executor()

    try:
        current_msgs = [HumanMessage(content=user_question.strip())]
        _log_payload(session_id, current_msgs)

        result = agent.invoke(
            {"messages": current_msgs},
            config={"configurable": {"session_id": session_id}},
        )
        # result is a list of messages; take the last AI message content
        if isinstance(result, list):
            last: BaseMessage = result[-1]
            answer_text = getattr(last, "content", str(last))
        else:
            answer_text = str(result)
        return ChatResponse(answer=answer_text, sources=None)
    except Exception as e:
        logger.error("Agent failed (session=%s): %s", session_id, e)
        return ChatResponse(answer="Error executing agent", sources=None)


# ---------------------------------------------------------------------------
# Streaming helper
# ---------------------------------------------------------------------------


def stream_agent_answer(user_question: str, session_id: str = "default") -> Generator[str, None, None]:
    """Yield agent answer chunks as they stream from the model."""
    if not user_question or not user_question.strip():
        yield "Question must not be empty."
        return

    agent = _build_agent_executor()

    current_msgs = [HumanMessage(content=user_question.strip())]
    _log_payload(session_id, current_msgs)

    # The agent's .stream returns events containing the messages list.
    for event in agent.stream(
        {"messages": current_msgs},
        config={"configurable": {"session_id": session_id}},
        stream_mode="values",
    ):
        try:
            # Each `event` is a dict with key "messages"; yield latest AI content.
            msgs = event.get("messages") if isinstance(event, dict) else None
            if msgs:
                ai_msg = msgs[-1]
                content = getattr(ai_msg, "content", str(ai_msg))
                yield content
            else:
                yield str(event)
        except Exception:
            yield str(event)


def _get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Fetch shared history for *session_id*."""
    return DEFAULT_HISTORY_STORE.get(session_id) 