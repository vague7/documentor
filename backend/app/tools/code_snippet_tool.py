# Built-ins
from functools import lru_cache
from typing import Literal, Optional

# Third-party
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Local
from app.config import get_settings

# ---------------------------------------------------------------------------
# Prompt template (chat-style for clarity & determinism)
# ---------------------------------------------------------------------------

_CODE_SNIPPET_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an assistant that writes minimal, runnable API code snippets from the docs uploaded by the user."
            " Return ONLY the code block (no explanation).",
        ),
        (
            "human",
            "Generate a {language} example using {client_lib} to call:\n"
            "  {method} {endpoint}\n"
            "Parameters (if any): {params}",
        ),
    ]
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Small in-memory cache for generated snippets (reduces repeated LLM calls in prod)
# Cache key is determined by the "public" function arguments so we simply rely on
# the default hashing of the parameter tuple. The result size is tiny so we keep
# a modest upper bound.

# NOTE: `lru_cache` is preferable to a manual dict so we get built-in tooling like
# `.cache_info()` & easy clearing in tests.


def _format_snippet(snippet: str, language: str) -> str:
    """Apply lightweight code-formatting to the snippet.

    * For Python we use `black` in library mode (if available).
    * For JavaScript we currently do a noop – can be extended with "prettier"
      via an API call or `jsbeautifier` if desired.
    * Other/unknown languages => return unchanged.
    """

    if language.lower() == "python":
        try:
            import black  # type: ignore

            # Black expects a valid top-level module string without backticks.
            # Users may request fenced code blocks – we strip them just in case.
            cleaned = snippet.strip().lstrip("```python").rstrip("``` ")
            formatted = black.format_str(cleaned, mode=black.FileMode())
            return formatted.rstrip()  # Trim the trailing newline Black adds
        except Exception:
            # If black isn't installed or formatting fails, fall back silently
            return snippet
    # TODO: integrate prettier/ruff/beautifier for JS snippets in future phases
    return snippet


def _raw_snippet_from_llm(
    *,
    endpoint: str,
    method: str,
    language: str,
    params: Optional[str],
    client_lib: str,
) -> str:
    """Single LLM invocation that returns an *unformatted* snippet string."""

    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=settings.gemini_api_key, temperature=0,
        convert_system_message_to_human=True,
    )

    chain = _CODE_SNIPPET_TEMPLATE | llm | StrOutputParser()

    return chain.invoke(
        {
            "language": language,
            "client_lib": client_lib,
            "method": method,
            "endpoint": endpoint,
            "params": params or "None",
        }
    )


@lru_cache(maxsize=128)
def _generate_snippet(
    endpoint: str,
    method: str,
    language: str,
    params: Optional[str],
    client_lib: str,
) -> str:
    """Generate (or retrieve from cache) a formatted snippet for given inputs."""

    # Step 1 – raw generation (may be slow & costly)
    raw = _raw_snippet_from_llm(
        endpoint=endpoint,
        method=method,
        language=language,
        params=params,
        client_lib=client_lib,
    )

    # Step 2 – post-process / format
    return _format_snippet(raw, language)

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

#TODO: add a description for the tool
@tool(description="Generate a language-specific code snippet for an API call.")
def code_snippet(
    endpoint: str,
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    language: Literal["python", "javascript"] = "python",
    params: Optional[str] = None,
    client_lib: str = "requests",
) -> str:
    """Generate a language-specific code snippet for an API call.

    Args:
        endpoint: The REST path, e.g. /users/{id}
        method: HTTP verb.
        language: Target language (python or javascript).
        params: Optional parameters description (query/body) as a string.
        client_lib: Preferred client library (default 'requests').

    Returns:
        A code snippet string.
    """

    # Use cached generator to ensure repeated identical calls don't hit the LLM.
    return _generate_snippet(
        endpoint=endpoint,
        method=method,
        language=language,
        params=params,
        client_lib=client_lib,
    )
