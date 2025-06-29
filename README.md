# DocuMentor – API-Documentation Assistant

DocuMentor is a reference implementation of a modern **Retrieval-Augmented Generation (RAG)** pipeline built with FastAPI & LangChain. It helps developers query their own API documentation and even generates code snippets or Postman requests via a developer-oriented agent.

---

## Public REST Endpoints

| Path               | Method | Description                                                                                               |
|--------------------|--------|-----------------------------------------------------------------------------------------------------------|
| `/chat`            | POST   | Conversational Q&A over your documentation (non-streaming).                                               |
| `/chat/stream`     | POST   | Same as above but returns Server-Sent Events (*text/plain*) for real-time streaming.                       |
| `/agent`           | POST   | Developer assistant agent that can run multiple tools (code-snippet, endpoint-suggester, **knowledge_search**). |
| `/agent/stream`    | POST   | Streaming variant of the agent.                                                                           |
| `/ingest`          | POST   | Trigger documentation ingestion into the vector store (internal/admin).                                   |
| `/health`          | GET    | Lightweight health probe.                                                                                 |

The full OpenAPI specification lives at `/openapi.json` and is visualised by Swagger UI at `/docs`.

---

## 🆕  Knowledge Search Tool

The agent is now **documentation-aware** through a LangChain tool called `knowledge_search` which performs retrieval on the vector store and returns the answer *directly* to the user.

* Accepts `question: str` and optional `session_id: str`.
* Enabled by default, can be disabled with the environment variable
  `KNOWLEDGE_TOOL_ENABLED="false"`.
* Provides detailed logging when `LOG_LEVEL=DEBUG`.

---

## 🗄️ Persistence Backends

Conversation history can be stored in-memory (default), SQLite, or **MongoDB Atlas**.

1. Set the backend via environment variable:
   ```bash
   HISTORY_BACKEND=mongo
   MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   ```
2. Run the helper to create indexes once:
   ```bash
   python -m backend.scripts.init_indexes
   ```
3. Start the API – both `/chat` and `/agent` will now share persistent history.

---

## Quick Demo

### Using cURL

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
        "user_question": "Give me a Python requests snippet that fetches a user by id using the /users/{id} endpoint.",
        "session_id": "demo"
      }'
```

### Using Postman

1. Create a new **POST** request to `{{baseUrl}}/agent/stream`.
2. Select *raw* ➜ *JSON* body and paste:
   ```json
   {
     "user_question": "What parameters does POST /orders accept?",
     "session_id": "demo"
   }
   ```
3. Send the request. In the response pane you will see a live stream of the
   answer. Look out for the agent's tool call – you'll notice that it invokes
   `knowledge_search` to fetch authoritative information before crafting the
   final reply.

---

## Local Development

```bash
# Install Python dependencies
cd backend/app
pip install -r requirements.txt

# Start the API
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` in your browser to explore interactively.

---

## License

Licensed under the Apache 2.0 License – see `LICENSE` for details. 