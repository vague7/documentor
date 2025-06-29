from typing import List

from langchain_core.tools import tool
from app.vector.chroma_client import get_vectorstore
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from app.config import get_settings

_SYSTEM_PROMPT = (
    "You are an API expert. Given a developer question and list of endpoints, "
    "return the single most relevant endpoint path. If none match, return 'NONE'."
)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_ENDPOINT_SUGGESTER_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        (
            "human",
            "Question: {question}\nEndpoints:\n{endpoints}\nAnswer:",
        ),
    ]
)


@tool
def endpoint_suggester(question: str, top_k: int = 5) -> str:
    """Suggest the best API endpoint for the given developer question."""
    # Retrieve candidate endpoint descriptions from vectorstore
    retriever = get_vectorstore().as_retriever(search_kwargs={"k": top_k})
    docs = retriever.invoke(question)
    endpoints: List[str] = [d.metadata.get("source", d.page_content) for d in docs]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=get_settings().gemini_api_key, temperature=0
    )

    chain = _ENDPOINT_SUGGESTER_TEMPLATE | llm | StrOutputParser()

    return chain.invoke({"question": question, "endpoints": "\n".join(endpoints)}).strip() 