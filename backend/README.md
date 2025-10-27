# Backend — FastAPI RAG Chatbot

FastAPI backend for intelligent document search (RAG), LLM chat with Mistral AI, weather queries, and MongoDB persistence.

## What This Does

AI chatbot that answers questions using uploaded documents (RAG), provides weather info, and maintains conversation history. Uses Mistral AI for chat/embeddings, FAISS for vector search, and MongoDB for storage.

## Quick Setup

Clone and install (Windows PowerShell):

```powershell
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install and start MongoDB:

```powershell
# Install via Chocolatey (if not installed: https://chocolatey.org/install)
choco install mongodb

# Start MongoDB service
net start MongoDB
```

You can also download MongoDB manually from the following link:
➡️ **Direct download:** [MongoDB Windows Installer (v8.2.1)](https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.2.1-signed.msi)

If it didn’t work, go to the official MongoDB website and download it here:
🌐 **Official site:** [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)

After downloading:

1. Open MongoDB Compass or your MongoDB client.
2. Click **“Add New Connection.”**
3. Copy the connection URL and paste it into your `.env` file under `MONGODB_URL`.
4. (Optional) Enter a name for your connection.
5. Press **Save and Connect.**
6. You are now connected to the database ✅

Create `.env` file in `backend/` folder with required keys:

```env
MISTRAL_API_KEY=your_key_here
MONGODB_URL=mongodb://localhost:27017
```

Run the backend:

```powershell
python main.py
```

Visit [http://127.0.0.1:8011/docs](http://127.0.0.1:8011/docs) for interactive API documentation.

## Configuration Reference

All settings in `core/config.py` (customize via `.env` file):

**Server Settings**

* `HOST` — Server bind address (default: 127.0.0.1)
* `PORT` — Server port (default: 8011)
* `RELOAD` — Auto-reload on code changes (default: true)
* `LOG_LEVEL` — Logging verbosity: debug, info, warning, error (default: info)

**Database Settings**

* `MONGODB_URL` — MongoDB connection string (default: mongodb://localhost:27017)
* `DATABASE_NAME` — MongoDB database name (default: bot_database)
* `DATABASE_TIMEOUT_MS` — Database connection timeout in milliseconds (default: 5000)

**Mistral AI Settings**

* `MISTRAL_API_ENDPOINT` — Mistral chat completions API URL (default: [https://api.mistral.ai/v1/chat/completions](https://api.mistral.ai/v1/chat/completions))
* `MISTRAL_API_KEY` — Mistral API key for authentication (required)
* `MISTRAL_MODEL` — Mistral chat model name (default: mistral-small-2503)
* `MISTRAL_API_EMBEDDING` — Mistral embeddings API URL (default: [https://api.mistral.ai/v1/embeddings](https://api.mistral.ai/v1/embeddings))
* `MISTRAL_EMBEDDING_MODEL` — Embedding model name (default: codestral-embed)
* `MISTRAL_TEMPERATURE` — LLM creativity/randomness 0.0-1.0 (default: 0.7)
* `MISTRAL_MAX_TOKENS` — Maximum response length in tokens (default: 500)
* `MISTRAL_MAX_CONTEXT_TOKENS` — Maximum context window tokens (default: 10000)
* `MISTRAL_API_TIMEOUT` — Chat API timeout in seconds (default: 60.0)
* `MISTRAL_EMBEDDING_TIMEOUT` — Embedding API timeout in seconds (default: 120.0)
* `MISTRAL_STARTUP_TIMEOUT` — Startup health check timeout (default: 10.0)
* `MISTRAL_STARTUP_MAX_TOKENS` — Tokens for startup test (default: 10)
* `MISTRAL_MAX_RETRIES` — API retry attempts on failure (default: 3)
* `MISTRAL_EMBEDDING_BATCH_SIZE_SMALL` — Small batch size for embeddings (default: 5)
* `MISTRAL_EMBEDDING_BATCH_SIZE_LARGE` — Large batch size for embeddings (default: 10)
* `MISTRAL_EMBEDDING_BATCH_THRESHOLD` — Threshold to switch batch size (default: 50)

**Weather API Settings**

* `OPENWEATHER_API_KEY` — OpenWeatherMap API key (optional, for weather tool)
* `OPENWEATHER_API_URL` — Weather API endpoint (default: [https://api.openweathermap.org/data/2.5/weather](https://api.openweathermap.org/data/2.5/weather))
* `OPENWEATHER_API_TIMEOUT` — Weather API timeout in seconds (default: 30.0)

**RAG (Document Search) Settings**

* `RAG_MAX_CONTEXT_CHUNKS` — Max document chunks to retrieve (default: 5)
* `RAG_MAX_CONTEXT_LENGTH` — Max total context length in characters (default: 2000)
* `RAG_CHUNK_SIZE` — Document chunk size in characters (default: 500)
* `RAG_CHUNK_OVERLAP` — Overlap between chunks in characters (default: 50)

**Upload Settings**

* `MAX_UPLOAD_SIZE_MB` — Maximum file upload size in MB (default: 10)

**Other Settings**

* `SOCKET_TIMEOUT` — Network socket timeout in seconds (default: 1.0)
* `CHARS_PER_TOKEN` — Estimated characters per token for counting (default: 4)
* `STRICT_TOOL_MATCHING` — Prevent LLM hallucination by requiring tool match (default: true)
* `DEBUG_THIRD_PARTY` — Enable debug logs for libraries (default: false)
* `MINIMAL_LOGGING` — Use minimal clean logging (default: true)

## API Endpoints

**Main Chat Interface**

* `POST /api/orchestrator/query` — Send message and get AI response (with RAG/weather)

**User Management**

* `POST /api/users/` — Create user
* `GET /api/users/` — List all users
* `GET /api/users/{user_id}` — Get user details

**Document Management**

* `POST /api/documents/upload` — Upload document for RAG search
* `GET /api/documents/user/{user_id}` — List user's documents
* `DELETE /api/documents/{document_id}` — Delete document

**Messages**

* `GET /api/messages/user/{user_id}` — Get conversation history

**Health**

* `GET /health` — Backend health check

## Project Structure

```
backend/
├── startup.py              # Entry point with health checks
├── main.py                 # FastAPI app initialization
├── core/
│   ├── config.py          # Configuration settings
│   ├── orchestrator.py    # Main request handler
│   ├── mistral_service.py # Mistral AI integration
│   ├── rag_service.py     # Document search
│   └── bot_tools/         # Weather & RAG tools
├── database/              # MongoDB adapter
├── routes/                # API endpoints
├── logs/                  # Application logs
└── vector_storage/        # FAISS vector indexes
```
