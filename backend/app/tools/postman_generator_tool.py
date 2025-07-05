import json
from typing import List

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import get_settings

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_POSTMAN_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an assistant that creates minimal Postman v2.1 collections in JSON. "
            "Return ONLY valid JSON. Include variables for baseUrl. Collection name: {name}.",
        ),
        (
            "human",
            "Generate a Postman collection containing the following endpoints:\n{endpoints}\n"
            "Use {{baseUrl}} variable. Ensure output is raw JSON for Postman v2.1.",
        ),
    ]
)


@tool(description="Generate a Postman collection JSON for the provided endpoints.")
def postman_generator(name: str, endpoints: List[str]) -> str:
    """Generate a Postman collection JSON for the provided endpoints."""
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=settings.gemini_api_key, temperature=0,
        convert_system_message_to_human=True,
    )

    chain = _POSTMAN_TEMPLATE | llm | StrOutputParser()

    raw_json = chain.invoke({"name": name, "endpoints": "\n".join(endpoints)})

    # Validate JSON
    try:
        json.loads(str(raw_json))
        return str(raw_json)
    except Exception:
        # If invalid, wrap as string
        return json.dumps({"error": "Invalid JSON returned"}) 