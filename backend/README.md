# Backend — Intelligent Chatbot API (concise)

FastAPI backend that provides LLM chat (Mistral), RAG document search, weather queries, and MongoDB storage.

Quick setup (local)
```powershell
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create .env (see variables below)
python startup.py
```

Start MongoDB locally (options)
- Windows (Chocolatey): `choco install mongodb` then `net start MongoDB`
- macOS (Homebrew): `brew tap mongodb/brew && brew install mongodb-community && brew services start mongodb-community`
- Linux (apt): `sudo apt-get install -y mongodb && sudo systemctl start mongodb`
- Or use MongoDB Atlas (cloud)

One-line environment variables (put in `backend/.env`)
- MISTRAL_API_KEY — Mistral API key
- MONGODB_URL — MongoDB connection string
- DATABASE_NAME — MongoDB DB name
- HOST — Server host (default 127.0.0.1)
- PORT — Server port (default 8011)
# Purpose: Required for LLM chat completions and generating text embeddings

---# How to get: Sign up at https://console.mistral.ai/ and create an API key

# Example: MISTRAL_API_KEY=sk-abc123xyz789

## How It Works

# MongoDB Connection URL


# Backend — FastAPI (concise)

FastAPI backend for document ingestion, embeddings, vector search and chat (RAG) using Mistral + FAISS + MongoDB.

Quick setup

```powershell
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create backend/.env (see variables below)
python startup.py
```

One-line environment variables (put in `backend/.env`)
- MISTRAL_API_KEY — API key used for Mistral inference calls
- MISTRAL_EMBEDDING_KEY — API key used to create embeddings
- MONGODB_URI — MongoDB connection string (e.g. mongodb://localhost:27017)
- VECTOR_STORE_PATH — Local directory to persist vector index files
- RAG_K — Number of top documents to retrieve for RAG (integer)
- UPLOAD_DIR — Directory where uploaded documents are stored
- LOG_LEVEL — Logging level (DEBUG, INFO, WARNING, ERROR)

Short run & MongoDB notes
- Start MongoDB locally: run the MongoDB service or use Docker: `docker run -d -p 27017:27017 --name mongo mongo:6`.
- Ensure `MONGODB_URI` points to your running MongoDB instance before starting the backend.

Important endpoints (short)
- GET /health — Health check
- POST /upload — Upload documents (multipart/form-data)
- POST /chat — Send chat messages; backend performs RAG and replies

Support: https://github.com/Mohamadaliibrahim/fastapi_mini_project/issues
- MAX_UPLOAD_SIZE_MB — Max upload size (MB)
- OPENWEATHER_API_KEY — (optional) OpenWeather API key
- STRICT_TOOL_MATCHING — true to avoid hallucinations

Useful endpoints
- POST /users/ — create user
- POST /documents/upload?user_id={id} — upload file
- POST /orchestrator/process — chat endpoint
- GET /messages/{user_id} — conversation history
- GET /health — health check

Notes
- API docs available at /docs when running
- For production: use MongoDB Atlas, set RELOAD=false, run behind a reverse proxy and process manager

Support: https://github.com/Mohamadaliibrahim/fastapi_mini_project/issues

### Optional Variables (RAG Configuration)

```env
# ============================================
# RAG (DOCUMENT SEARCH) CONFIGURATION
# ============================================

# Maximum Context Chunks to Retrieve
RAG_MAX_CONTEXT_CHUNKS=5
# Description: Maximum number of document chunks to retrieve for a query
# Purpose: Limits how many relevant text pieces are included in context
# Trade-offs:
#   - More chunks (10+): Better context, but slower and uses more tokens
#   - Fewer chunks (3-5): Faster, focused answers
# Typical values:
#   - 3-5: Fast, focused answers (recommended)
#   - 5-10: Comprehensive answers
#   - 10+: Deep research (may hit token limits)
# Default: 5
# Example: RAG_MAX_CONTEXT_CHUNKS=10

# Maximum Context Length (characters)
RAG_MAX_CONTEXT_LENGTH=2000
# Description: Maximum total character length of all retrieved chunks
# Purpose: Limits combined length to prevent token overflow
# Default: 2000 characters
# Example: RAG_MAX_CONTEXT_LENGTH=3000

# Text Chunk Size (characters)
RAG_CHUNK_SIZE=500
# Description: Size of text chunks when splitting documents
# Purpose: Determines granularity of document search
# Trade-offs:
#   - Smaller (200-300): More precise, granular search
#   - Medium (500-800): Balanced (recommended)
#   - Larger (1000+): More context per chunk, less precise
# Default: 500
# Example: RAG_CHUNK_SIZE=800

# Chunk Overlap (characters)
RAG_CHUNK_OVERLAP=50
# Description: How many characters overlap between consecutive chunks
# Purpose: Prevents splitting sentences/paragraphs awkwardly
# Typical: 10-20% of chunk size
# Default: 50
# Example: RAG_CHUNK_OVERLAP=100
```

---

### Optional Variables (Upload & Weather Configuration)

```env
# ============================================
# UPLOAD CONFIGURATION
# ============================================

# Maximum Upload File Size (MB)
MAX_UPLOAD_SIZE_MB=10
# Description: Maximum file size users can upload
# Purpose: Limits document size to prevent resource exhaustion
# Trade-offs:
#   - Larger files take longer to process
#   - More embeddings cost more money
# Default: 10 MB
# Example: MAX_UPLOAD_SIZE_MB=50

# ============================================
# WEATHER API CONFIGURATION
# ============================================

# OpenWeatherMap API URL
OPENWEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather
# Description: OpenWeatherMap API endpoint for weather data
# Purpose: URL for fetching current weather information
# Default: https://api.openweathermap.org/data/2.5/weather
# Example: OPENWEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather

# Weather API Timeout (seconds)
OPENWEATHER_API_TIMEOUT=30.0
# Description: How long to wait for weather API response
# Purpose: Prevents hanging on slow weather API calls
# Default: 30.0 seconds
# Example: OPENWEATHER_API_TIMEOUT=45.0
```

---

### Optional Variables (Logging & Misc)

```env
# ============================================
# LOGGING CONFIGURATION
# ============================================

# Debug Third-Party Libraries
DEBUG_THIRD_PARTY=false
# Description: Enable debug logging for third-party libraries
# Purpose: Shows detailed logs from httpx, motor, etc.
# Options: true (verbose), false (clean)
# Default: false
# Use case: Debugging library-related issues
# Example: DEBUG_THIRD_PARTY=true

# Minimal Logging Mode
MINIMAL_LOGGING=true
# Description: Use minimal logging for cleaner output
# Purpose: Reduces log verbosity
# Options: true (clean), false (detailed)
# Default: true
# Example: MINIMAL_LOGGING=false

# ============================================
# ORCHESTRATOR CONFIGURATION
# ============================================

# Strict Tool Matching
STRICT_TOOL_MATCHING=true
# Description: Require exact tool matches (anti-hallucination)
# Purpose: Controls whether LLM can answer outside tool scope
# Options:
#   - true: LLM must select a tool or return "I don't know" (recommended)
#   - false: LLM can answer general questions (may hallucinate)
# Default: true
# Example: STRICT_TOOL_MATCHING=false

# ============================================
# TOKEN ESTIMATION
# ============================================

# Characters Per Token
CHARS_PER_TOKEN=4
# Description: Estimated characters per token for token counting
# Purpose: Used to estimate token usage from text length
# Default: 4 (standard estimate for English)
# Note: Actual ratio varies by language and tokenizer
# Example: CHARS_PER_TOKEN=4
```

---

## Usage

### Starting the Backend

Once configured, start the backend server:

```bash
python startup.py
```

The application will:
1. Load environment variables from `.env`
2. Validate all required API keys
3. Check MongoDB connectivity
4. Verify Mistral AI API access
5. Start the FastAPI server

**Access Points:**
- **API Server**: http://127.0.0.1:8011
- **Interactive API Docs (Swagger)**: http://127.0.0.1:8011/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8011/redoc

### Basic API Calls

**Create a User:**
```bash
curl -X POST "http://127.0.0.1:8011/api/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "email": "john@example.com"}'
```

**Upload a Document:**
```bash
curl -X POST "http://127.0.0.1:8011/api/documents/upload" \
  -F "file=@document.pdf" \
  -F "user_id=user_123"
```

**Chat with the Bot:**
```bash
curl -X POST "http://127.0.0.1:8011/api/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_input": "What is the weather in Paris?"
  }'
```

---

## API Documentation

The backend provides comprehensive API documentation through FastAPI's built-in Swagger UI.

### Access Interactive Documentation:

Visit **http://127.0.0.1:8011/docs** in your browser to:
- View all available endpoints
- See request/response schemas
- Test API calls directly in the browser
- Download OpenAPI specification

### Main API Endpoints:

**User Management:**
- `POST /api/users/` - Create a new user
- `GET /api/users/` - List all users
- `GET /api/users/{user_id}` - Get specific user details

**Document Management:**
- `POST /api/documents/upload` - Upload a document for RAG search
- `GET /api/documents/user/{user_id}` - List user's documents
- `DELETE /api/documents/{document_id}` - Delete a document

**Messaging:**
- `POST /api/messages/` - Send a message to the bot
- `GET /api/messages/user/{user_id}` - Get conversation history

**Orchestrator (Main Bot Interface):**
- `POST /api/orchestrator/query` - Main endpoint for chatting with the bot

**Health Check:**
- `GET /health` - Check if the backend is running

---

## Manual Deployment

For deploying the backend to a production server:

### 1. Server Setup

```bash
# SSH into your server
ssh user@your-server.com

# Clone the repository
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project/backend
```

### 2. Install Dependencies

```bash
python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Production Environment

```bash
# Create .env file with production settings
nano .env
```

Set production values:
```env
HOST=0.0.0.0  # Allow external access
PORT=8011
RELOAD=false  # Disable auto-reload in production
LOG_LEVEL=warning  # Less verbose logging
MISTRAL_API_KEY=your_production_key
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
# ... other production settings
```

### 4. Run with Process Manager

**Using systemd:**

Create `/etc/systemd/system/chatbot-backend.service`:
```ini
[Unit]
Description=Chatbot Backend API
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/fastapi_mini_project/backend
Environment="PATH=/path/to/myvenv/bin"
ExecStart=/path/to/myvenv/bin/python startup.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable chatbot-backend
sudo systemctl start chatbot-backend
sudo systemctl status chatbot-backend
```

**Or using PM2:**
```bash
pm2 start startup.py --name chatbot-backend --interpreter python
pm2 save
pm2 startup
```

---

## Tests

### Running Tests

(Note: Test files should be created in a `tests/` directory)

```bash
# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=routes --cov=database

# Run specific test file
pytest tests/test_orchestrator.py

# Run with verbose output
pytest -v
```

### Manual Testing

**Test Health Check:**
```bash
curl http://127.0.0.1:8011/health
```

**Test Tool Selection:**
```bash
# Should select weather_tool
curl -X POST "http://127.0.0.1:8011/api/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_input": "Weather in London"}'

# Should select rag_tool
curl -X POST "http://127.0.0.1:8011/api/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_input": "Search documents for pricing"}'

# Should return "I don't know"
curl -X POST "http://127.0.0.1:8011/api/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_input": "What is 2+2?"}'
```

---

## Project Structure

```
backend/
├── startup.py                 # Application entry point with health checks
├── main.py                    # FastAPI application initialization
├── prompts.txt               # Centralized LLM prompts
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
│
├── core/                     # Core business logic
│   ├── config.py            # Configuration management
│   ├── orchestrator.py      # Main request orchestrator
│   ├── mistral_service.py   # Mistral AI integration
│   ├── rag_service.py       # Document search service
│   ├── embedding_service.py # Embedding generation
│   ├── document_processor.py# Document processing
│   ├── prompt_loader.py     # Prompt management
│   ├── logger.py            # Logging configuration
│   ├── rag_utils.py         # RAG utilities
│   ├── crud.py              # Database operations
│   │
│   └── bot_tools/           # Modular bot tools
│       ├── weather_tool.py  # Weather queries
│       └── rag_tool.py      # Document search
│
├── database/                 # Database layer
│   ├── interface.py         # Database interface
│   ├── factory.py           # Database factory pattern
│   └── mongodb_adapter.py   # MongoDB implementation
│
├── routes/                   # API endpoints
│   ├── orchestrator.py      # Orchestrator endpoints
│   ├── documents.py         # Document management
│   ├── users.py             # User management
│   ├── messages.py          # Message handling
│   └── basic.py             # Health checks
│
├── logs/                     # Application logs
│   ├── debug.txt            # Debug information
│   ├── error.txt            # Error logs
│   ├── prompt.txt           # LLM interactions
│   └── timing.txt           # Performance metrics
│
└── vector_storage/           # Vector embeddings storage
    └── [user_id]/           # User-specific vector stores
```

---

## Troubleshooting

**Port Already in Use:**
```env
# Change PORT in .env
PORT=8012
```

**MongoDB Connection Failed:**
```bash
# Windows
net start MongoDB

# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

**Mistral API Key Invalid:**
- Verify key in `.env` file
- Check for extra spaces
- Ensure key is active at https://console.mistral.ai/

**Module Not Found:**
```bash
pip install -r requirements.txt
```

**Check Application Logs:**
- `logs/error.txt` - Error messages
- `logs/debug.txt` - Debug information
- `logs/prompt.txt` - LLM interactions
- `logs/timing.txt` - Performance data

---

## License

MIT License - Copyright (c) 2025 Mohamad Ali Ibrahim
