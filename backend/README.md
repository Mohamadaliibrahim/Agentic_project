Perfect — here is the **cleaned, main-README-ready Backend section**, rewritten so it can live **inside the original root README**, with **all git / clone / cd references removed**, exactly like we did for the frontend.

You can paste this directly under a **“Backend — FastAPI RAG Chatbot”** section in your main `README.md`.

---

## Backend — FastAPI RAG Chatbot

FastAPI backend that powers the AI chatbot.
Handles **RAG (document search)**, **LLM chat via Mistral AI**, **weather queries**, and **MongoDB persistence**.

---

### What This Does

* Answers questions using uploaded documents (RAG)
* Integrates Mistral AI for chat & embeddings
* Uses FAISS for vector similarity search
* Stores users, documents, and conversations in MongoDB
* Provides tool-based orchestration (RAG + weather)

---

### Backend Setup

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### MongoDB Setup

Install MongoDB Community Edition from the official site:
[https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)

After installation:

1. Open **MongoDB Compass** (or another MongoDB client)
2. Click **Add New Connection**
3. Copy the connection URL
4. Use it in your `.env` file under `MONGODB_URL`
5. Save and connect

You are now connected to MongoDB ✅

---

### Environment Variables

Create a `.env` file inside the `backend/` directory:

```env
MISTRAL_API_KEY=your_key_here
MONGODB_URL=mongodb://localhost:27017
```

---

### Run Backend

Start the FastAPI server:

```powershell
python main.py
```

Interactive API documentation is available at:

```
http://127.0.0.1:8011/docs
```

---

### Configuration Reference

All backend settings are defined in `core/config.py` and can be overridden using environment variables.

#### Server Settings

* `HOST` — Server bind address (default: 127.0.0.1)
* `PORT` — Server port (default: 8011)
* `RELOAD` — Auto-reload on code changes (default: true)
* `LOG_LEVEL` — Logging level (default: info)

#### Database Settings

* `MONGODB_URL` — MongoDB connection string
* `DATABASE_NAME` — Database name (default: bot_database)
* `DATABASE_TIMEOUT_MS` — Connection timeout (default: 5000 ms)

#### Mistral AI Settings

* `MISTRAL_API_KEY` — **Required**
* `MISTRAL_MODEL` — Chat model (default: mistral-small-2503)
* `MISTRAL_EMBEDDING_MODEL` — Embedding model (default: codestral-embed)
* `MISTRAL_TEMPERATURE` — Response creativity (default: 0.7)
* `MISTRAL_MAX_TOKENS` — Max response tokens (default: 500)
* `MISTRAL_MAX_CONTEXT_TOKENS` — Context window limit
* Retry, timeout, and batch-size controls for stability

#### Weather API (Optional)

* `OPENWEATHER_API_KEY`
* `OPENWEATHER_API_URL`
* `OPENWEATHER_API_TIMEOUT`

#### RAG (Document Search)

* `RAG_MAX_CONTEXT_CHUNKS`
* `RAG_MAX_CONTEXT_LENGTH`
* `RAG_CHUNK_SIZE`
* `RAG_CHUNK_OVERLAP`

#### Upload Settings

* `MAX_UPLOAD_SIZE_MB` — Default: 10 MB

#### Other

* `STRICT_TOOL_MATCHING` — Prevent hallucinations
* `MINIMAL_LOGGING` — Clean log output
* `DEBUG_THIRD_PARTY` — Debug external libraries

---

### API Endpoints

#### Main Chat

* `POST /api/orchestrator/query` — Chat with AI (RAG + tools)

#### Users

* `POST /api/users/` — Create user
* `GET /api/users/` — List users
* `GET /api/users/{user_id}` — User details

#### Documents

* `POST /api/documents/upload` — Upload document
* `GET /api/documents/user/{user_id}` — List user documents
* `DELETE /api/documents/{document_id}` — Delete document

#### Messages

* `GET /api/messages/user/{user_id}` — Conversation history

#### Health

* `GET /health` — Backend health check

---

### Backend Structure

```
backend/
├── startup.py              # Startup & health checks
├── main.py                 # FastAPI app initialization
├── core/
│   ├── config.py           # Configuration
│   ├── orchestrator.py     # Request orchestration
│   ├── mistral_service.py  # LLM integration
│   ├── rag_service.py      # Document retrieval
│   └── bot_tools/          # Weather & RAG tools
├── database/               # MongoDB adapter
├── routes/                 # API routes
├── logs/                   # Application logs
└── vector_storage/         # FAISS vector indexes
```