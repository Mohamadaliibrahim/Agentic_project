# Assistant Chatbot Backend

An intelligent FastAPI-based backend service that provides LLM-powered orchestration, RAG (Retrieval-Augmented Generation) document search, and weather queries using Mistral AI.

## Description

This backend service is the core engine of an intelligent assistant chatbot system. It leverages Large Language Models (LLM) to intelligently route user queries to appropriate tools, search through uploaded documents using semantic embeddings, and provide real-time weather information. The system is designed with anti-hallucination features to ensure responses are limited to its available capabilities.

**Key Capabilities:**
- **Intelligent Tool Selection**: Uses Mistral AI to automatically determine which tool (weather, document search, or none) should handle each user query
- **RAG Document Search**: Implements semantic search using vector embeddings to find relevant information in uploaded documents
- **Weather Information**: Provides real-time weather data for any location via OpenWeatherMap API
- **Anti-Hallucination**: Prevents the AI from making up answers outside its tool capabilities
- **Centralized Configuration**: All settings managed through environment variables with zero hardcoded values
- **Production-Ready**: Includes comprehensive logging, error handling, and startup health checks

## Badges

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Installation

### Requirements

Before installing, ensure you have:
- **Python 3.12 or higher** installed
- **MongoDB** (local installation or MongoDB Atlas account)
- **Git** for version control
- **pip** for package management
- **API Keys**:
  - Mistral AI API key from [console.mistral.ai](https://console.mistral.ai/)
  - OpenWeatherMap API key from [openweathermap.org](https://openweathermap.org/api)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project/backend
```

### Step 2: Create Virtual Environment

**On Windows:**
```powershell
python -m venv ..\myvenv
..\myvenv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv ../myvenv
source ../myvenv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI - Web framework
- Uvicorn - ASGI server
- Motor - Async MongoDB driver
- Mistral AI SDK - LLM integration
- Chromadb - Vector database
- LangChain - Document processing
- And more...

### Step 4: Configure Environment Variables

Create a `.env` file in the `backend` directory:

**On Windows:**
```powershell
New-Item .env -ItemType File
notepad .env
```

**On macOS/Linux:**
```bash
touch .env
nano .env
```

Add the following configuration:

```env
# ============================================
# REQUIRED CONFIGURATION
# ============================================

# Mistral AI API Key
MISTRAL_API_KEY=your_mistral_api_key_here

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=bot_database

# OpenWeatherMap API Key
OPENWEATHER_API_KEY=your_openweather_api_key_here

# ============================================
# OPTIONAL CONFIGURATION (with defaults)
# ============================================

# Server Configuration
PORT=8011
HOST=127.0.0.1
RELOAD=true
LOG_LEVEL=info

# Mistral AI Settings
MISTRAL_MODEL=mistral-small-2503
MISTRAL_TEMPERATURE=0.7
MISTRAL_MAX_TOKENS=500

# RAG Configuration
RAG_MAX_CONTEXT_CHUNKS=5
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50

# Upload Configuration
MAX_UPLOAD_SIZE_MB=10
```

### Step 5: Start MongoDB

Ensure MongoDB is running:

**On Windows:**
```powershell
net start MongoDB
```

**On macOS:**
```bash
brew services start mongodb-community
```

**On Linux:**
```bash
sudo systemctl start mongod
```

### Step 6: Run the Backend

```bash
python startup.py
```

The backend will be available at:
- **API Server**: `http://127.0.0.1:8011`
- **API Documentation**: `http://127.0.0.1:8011/docs`
- **Alternative Docs**: `http://127.0.0.1:8011/redoc`

## Usage

### API Endpoints

Once the backend is running, you can interact with it through the following endpoints:

#### User Management
```bash
# Create a new user
curl -X POST "http://127.0.0.1:8011/api/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "email": "john@example.com"}'

# Get all users
curl "http://127.0.0.1:8011/api/users/"

# Get specific user
curl "http://127.0.0.1:8011/api/users/{user_id}"
```

#### Document Management
```bash
# Upload a document
curl -X POST "http://127.0.0.1:8011/api/documents/upload" \
  -F "file=@document.pdf" \
  -F "user_id=user_123"

# Get user documents
curl "http://127.0.0.1:8011/api/documents/user/{user_id}"

# Delete a document
curl -X DELETE "http://127.0.0.1:8011/api/documents/{document_id}"
```

#### Chat with the Bot
```bash
# Send a message
curl -X POST "http://127.0.0.1:8011/api/messages/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "content": "What is the weather in Paris?"
  }'

# Get conversation history
curl "http://127.0.0.1:8011/api/messages/user/{user_id}"
```

#### Orchestrator (Main Bot Interface)
```bash
# Query the intelligent orchestrator
curl -X POST "http://127.0.0.1:8011/api/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_input": "Search my documents for pricing information"
  }'
```

### Example Queries

**Weather Query:**
```json
{
  "user_id": "user_123",
  "user_input": "What's the weather in London?"
}
```
→ System selects `weather_tool` and returns current weather data

**Document Search:**
```json
{
  "user_id": "user_123",
  "user_input": "Find information about contracts in my documents"
}
```
→ System selects `rag_tool` and searches uploaded documents

**Unknown Query:**
```json
{
  "user_id": "user_123",
  "user_input": "What is 2+2?"
}
```
→ System returns "I don't know" (anti-hallucination feature)

### Interactive API Documentation

Visit `http://127.0.0.1:8011/docs` for interactive API documentation where you can:
- View all available endpoints
- Test API calls directly in the browser
- See request/response schemas
- Download OpenAPI specification

---

## 🏗️ Architecture

```
User Request → Orchestrator (LLM) → Tool Selection
                                       ├─ Weather Tool
                                       ├─ RAG Tool
                                       └─ Unknown → "I don't know"
```

**Key Files:**
- `core/orchestrator.py` - Main request router
- `core/bot_tools/` - Weather & RAG tools
- `core/rag_service.py` - Document embedding/search
- `core/mistral_service.py` - LLM API calls
- `core/prompt_loader.py` - Prompt management
- `prompts.txt` - All LLM prompts

---

## � API Endpoints

### Users
- `POST /api/users/` - Create user
- `GET /api/users/` - List users
- `GET /api/users/{user_id}` - Get user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/user/{user_id}` - List user documents
- `DELETE /api/documents/{document_id}` - Delete document

### Messages
- `POST /api/messages/` - Send message to bot
- `GET /api/messages/user/{user_id}` - Get conversation history

### Orchestrator
- `POST /api/orchestrator/query` - Main bot query endpoint

**Full API Docs:** `http://127.0.0.1:8011/docs`

---

## 📂 Project Structure

```
backend/
├── startup.py              # Application entry point
├── main.py                 # FastAPI app initialization
├── prompts.txt            # All LLM prompts
├── requirements.txt       # Python dependencies
├── core/
│   ├── config.py          # Configuration settings
│   ├── orchestrator.py    # Main request orchestrator
│   ├── mistral_service.py # LLM API service
│   ├── rag_service.py     # Document search service
│   ├── embedding_service.py # Embedding generation
│   ├── prompt_loader.py   # Prompt management
│   ├── logger.py          # Logging configuration
│   ├── rag_utils.py       # RAG utilities
│   └── bot_tools/
│       ├── weather_tool.py # Weather queries
│       └── rag_tool.py     # Document search
├── database/
│   ├── interface.py       # Database interface
│   ├── factory.py         # Database factory
│   └── mongodb_adapter.py # MongoDB implementation
├── routes/
│   ├── users.py           # User endpoints
│   ├── documents.py       # Document endpoints
│   ├── messages.py        # Message endpoints
│   └── orchestrator.py    # Orchestrator endpoints
└── logs/                  # Application logs
```

---

## Visuals

### Architecture Flow

```
┌─────────────┐
│ User Request│
└──────┬──────┘
       │
       ▼
┌───────────────────────────┐
│   Orchestrator (LLM)      │
│ Analyzes & selects tool   │
└──────┬────────────────────┘
       │
       ├──────────┬──────────┬───────────┐
       ▼          ▼          ▼           ▼
  ┌─────────┐ ┌──────┐ ┌─────────┐ ┌─────────┐
  │Weather  │ │ RAG  │ │  None   │ │ Future  │
  │  Tool   │ │Tool  │ │"I don't │ │ Tools   │
  │         │ │      │ │ know"   │ │         │
  └────┬────┘ └───┬──┘ └─────────┘ └─────────┘
       │          │
       ▼          ▼
  ┌─────────┐ ┌──────────┐
  │OpenWeather ChromaDB │
  │   API   │ │Vector DB │
  └────┬────┘ └────┬─────┘
       │           │
       └─────┬─────┘
             ▼
       ┌───────────┐
       │ LLM Format│
       │  Response │
       └─────┬─────┘
             ▼
       ┌───────────┐
       │   Return  │
       │ to User   │
       └───────────┘
```

### Key Components Interaction

1. **User Request** → Enters through API endpoint
2. **Orchestrator** → LLM analyzes intent and selects appropriate tool
3. **Tool Execution** → Fetches data from external APIs or vector database
4. **Response Formatting** → LLM formats the raw data into natural language
5. **User Response** → Clean, formatted answer delivered back

---

## Support

### Getting Help

If you encounter issues or have questions:

1. **Documentation**: Check this README and inline code comments
2. **API Docs**: Visit `http://127.0.0.1:8011/docs` for endpoint documentation
3. **Logs**: Review logs in the `logs/` directory:
   - `error.txt` - Error messages
   - `debug.txt` - Debug information
   - `prompt.txt` - LLM interactions
   - `timing.txt` - Performance metrics
4. **GitHub Issues**: [Report bugs or request features](https://github.com/Mohamadaliibrahim/fastapi_mini_project/issues)
5. **Email**: Contact the development team

### Common Support Topics

- Configuration issues
- API integration problems
- MongoDB connection errors
- Mistral AI API troubleshooting
- Performance optimization

---

## Roadmap

### Current Version (v1.0)
- ✅ Intelligent tool selection using LLM
- ✅ RAG document search
- ✅ Weather information queries
- ✅ Anti-hallucination features
- ✅ Centralized configuration management
- ✅ Comprehensive logging

### Planned Features (v1.1)
- 🔄 Multi-language support
- 🔄 Additional bot tools (calculator, unit converter, etc.)
- 🔄 Enhanced document processing (tables, images)
- 🔄 User authentication and authorization
- 🔄 Rate limiting and usage quotas
- 🔄 Caching for improved performance

### Future Considerations (v2.0+)
- 💡 Voice input/output support
- 💡 Real-time streaming responses
- 💡 Multi-modal capabilities (image understanding)
- 💡 Integration with more external APIs
- 💡 Advanced analytics and reporting
- 💡 Docker containerization
- 💡 Kubernetes deployment support

---

## Contributing

We welcome contributions to improve the Assistant Chatbot Backend!

### How to Contribute

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/fastapi_mini_project.git
   cd fastapi_mini_project/backend
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Run tests
   python -m pytest
   
   # Test manually
   python startup.py
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Then create a Pull Request on GitHub
   ```

### Contribution Guidelines

- **Code Quality**: Maintain clean, readable, and well-documented code
- **Testing**: Add tests for new features
- **Documentation**: Update README and inline comments
- **Commit Messages**: Use clear, descriptive commit messages
- **Pull Requests**: Provide detailed description of changes

### Code Style

- Follow PEP 8 for Python code
- Use type hints where applicable
- Keep functions focused and single-purpose
- Add docstrings to all functions and classes

---

## Authors and Acknowledgments

### Main Contributors
- **Mohamad Ali Ibrahim** - Initial development and architecture

### Acknowledgments
- **Mistral AI** - For providing powerful LLM capabilities
- **FastAPI** - For the excellent web framework
- **LangChain** - For document processing tools
- **ChromaDB** - For vector storage solution
- **MongoDB** - For reliable data persistence

### Special Thanks
- The open-source community for their invaluable tools and libraries
- All contributors who have helped improve this project

---

## License

This project is licensed under the MIT License.

### MIT License

```
MIT License

Copyright (c) 2025 Mohamad Ali Ibrahim

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Project Status

🟢 **Active Development** - This project is actively maintained and under continuous development.

### Current Status
- **Version**: 1.0.0
- **Last Updated**: October 2025
- **Maintenance**: Active
- **Production Ready**: Yes

### Development Activity
- Regular updates and improvements
- Bug fixes as reported
- New features in development (see Roadmap)
- Community contributions welcome

### Support Timeline
- **Active Support**: Current
- **Security Updates**: Ongoing
- **Feature Development**: Ongoing

For questions about the project status or future plans, please open an issue on GitHub.

---

## Configuration

All configuration is centralized in `core/config.py`. You can override any setting using environment variables.

### Key Configuration Files

1. **`core/config.py`**: Main configuration class with all settings
2. **`.env`**: Environment variables (create this file)
3. **`prompts.txt`**: All LLM prompts
4. **`requirements.txt`**: Python dependencies

---

## Environment Variables
```

---

**If using local MongoDB:**
```bash
# On Windows (if MongoDB is installed as a service)
net start MongoDB

# On macOS
brew services start mongodb-community

# On Linux
sudo systemctl start mongod
```

**If using MongoDB Atlas:**
- Ensure your connection string is in the `.env` file
- Whitelist your IP address in MongoDB Atlas

### Step 7: Run the Backend Server

```bash
python main.py
```

The backend will start on `http://127.0.0.1:8011`

---

## ⚙️ Configuration

All configuration is centralized in `core/config.py`. You can override any setting using environment variables.

### Key Configuration Files

1. **`core/config.py`**: Main configuration class with all settings
2. **`.env`**: Environment variables (create this file)
3. **`prompts.txt`**: All LLM prompts
4. **`requirements.txt`**: Python dependencies

---

## 🔐 Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

### Required Variables

```env
# ============================================
# REQUIRED CONFIGURATION
# ============================================

# Mistral AI API Key
MISTRAL_API_KEY=your_mistral_api_key_here
# Description: Your Mistral AI API authentication key for making LLM calls
# Purpose: Authenticates requests to Mistral AI's API for chat completions and embeddings
# Get it from: https://console.mistral.ai/
# Example: MISTRAL_API_KEY=sk-abc123xyz456def789

# MongoDB Connection String
MONGODB_URL=mongodb://localhost:27017
# Description: MongoDB database connection string
# Purpose: Connects to MongoDB for storing users, messages, and conversation data
# For local MongoDB: mongodb://localhost:27017
# For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
# Example: MONGODB_URL=mongodb://localhost:27017

# Database Name
DATABASE_NAME=bot_database
# Description: Name of the MongoDB database to use
# Purpose: Specifies which database within MongoDB to store application data
# Default: bot_database
# Example: DATABASE_NAME=my_bot_db

# OpenWeatherMap API Key
OPENWEATHER_API_KEY=your_openweather_api_key_here
# Description: API key for accessing OpenWeatherMap weather data
# Purpose: Enables the weather tool to fetch real-time weather information
# Get it from: https://openweathermap.org/api (free tier available)
# Example: OPENWEATHER_API_KEY=1234567890abcdef
```

---

### Optional Variables (Advanced Configuration)

#### Server Configuration

```env
HOST=127.0.0.1
# Description: Server host address
# Purpose: Defines the network interface the server listens on
# Default: 127.0.0.1 (localhost only)
# Options: 
#   - 127.0.0.1: Local access only
#   - 0.0.0.0: Allow external access
# Example: HOST=0.0.0.0

PORT=8011
# Description: Server port number
# Purpose: Defines which port the FastAPI server listens on
# Default: 8011
# Change if: Port is already in use by another application
# Example: PORT=8080

RELOAD=true
# Description: Enable auto-reload on code changes
# Purpose: Automatically restarts server when code files change (development feature)
# Default: true
# Options: true (development), false (production)
# Example: RELOAD=false

LOG_LEVEL=info
# Description: Logging verbosity level
# Purpose: Controls how much detail appears in logs
# Default: info
# Options: debug, info, warning, error, critical
# Example: LOG_LEVEL=debug
```

#### Database Configuration

```env
DATABASE_TYPE=mongodb
# Description: Type of database system
# Purpose: Specifies database adapter to use
# Default: mongodb
# Current support: mongodb only
# Example: DATABASE_TYPE=mongodb

DATABASE_TIMEOUT_MS=5000
# Description: Database connection timeout in milliseconds
# Purpose: How long to wait for database connection before failing
# Default: 5000 (5 seconds)
# Increase if: Database is slow or network is unstable
# Example: DATABASE_TIMEOUT_MS=10000
```

#### Mistral AI Configuration

```env
MISTRAL_API_ENDPOINT=https://api.mistral.ai/v1/chat/completions
# Description: Mistral AI chat completions API endpoint
# Purpose: URL for making LLM chat completion requests
# Default: https://api.mistral.ai/v1/chat/completions
# Change if: Using a custom/proxy endpoint
# Example: MISTRAL_API_ENDPOINT=https://api.mistral.ai/v1/chat/completions

MISTRAL_MODEL=mistral-small-2503
# Description: Mistral AI model to use for chat completions
# Purpose: Specifies which LLM model handles user queries and tool selection
# Default: mistral-small-2503
# Options: mistral-small-2503, mistral-medium, mistral-large
# Trade-off: Larger models = more accurate but slower and more expensive
# Example: MISTRAL_MODEL=mistral-large

MISTRAL_API_EMBEDDING=https://api.mistral.ai/v1/embeddings
# Description: Mistral AI embeddings API endpoint
# Purpose: URL for generating text embeddings for RAG search
# Default: https://api.mistral.ai/v1/embeddings
# Example: MISTRAL_API_EMBEDDING=https://api.mistral.ai/v1/embeddings

MISTRAL_EMBEDDING_MODEL=codestral-embed
# Description: Mistral AI model for generating embeddings
# Purpose: Converts text into vector embeddings for semantic search
# Default: codestral-embed
# Example: MISTRAL_EMBEDDING_MODEL=codestral-embed

MISTRAL_TEMPERATURE=0.7
# Description: LLM temperature (creativity/randomness)
# Purpose: Controls randomness in LLM responses
# Default: 0.7
# Range: 0.0 to 1.0
# - 0.0: Deterministic, factual, consistent
# - 0.5: Balanced between creativity and consistency
# - 1.0: More creative, varied, less predictable
# Use cases:
#   - 0.0-0.3: Factual Q&A, tool selection
#   - 0.4-0.7: General conversation (recommended)
#   - 0.8-1.0: Creative writing, brainstorming
# Example: MISTRAL_TEMPERATURE=0.5

MISTRAL_MAX_TOKENS=500
# Description: Maximum tokens in LLM response
# Purpose: Limits the length of AI-generated responses
# Default: 500
# Trade-off: Higher = longer responses but more expensive and slower
# Typical values:
#   - 100-300: Short, concise answers
#   - 500-1000: Standard answers
#   - 1000+: Detailed, comprehensive responses
# Example: MISTRAL_MAX_TOKENS=1000

MISTRAL_MAX_CONTEXT_TOKENS=10000
# Description: Maximum tokens in conversation context
# Purpose: Limits total conversation history sent to LLM
# Default: 10000
# Purpose: Prevents exceeding model context window
# Example: MISTRAL_MAX_CONTEXT_TOKENS=15000

MISTRAL_API_TIMEOUT=60.0
# Description: Timeout for Mistral API requests (seconds)
# Purpose: How long to wait for LLM response before timeout
# Default: 60.0 seconds
# Increase if: Getting frequent timeouts on complex queries
# Example: MISTRAL_API_TIMEOUT=120.0

MISTRAL_EMBEDDING_TIMEOUT=120.0
# Description: Timeout for embedding generation requests (seconds)
# Purpose: How long to wait for embedding generation (takes longer than chat)
# Default: 120.0 seconds (2 minutes)
# Note: Embeddings typically take longer, especially for large documents
# Example: MISTRAL_EMBEDDING_TIMEOUT=180.0

MISTRAL_STARTUP_TIMEOUT=10.0
# Description: Timeout for startup health check (seconds)
# Purpose: How long startup check waits for Mistral API test
# Default: 10.0 seconds
# Example: MISTRAL_STARTUP_TIMEOUT=15.0

MISTRAL_STARTUP_MAX_TOKENS=10
# Description: Max tokens for startup test request
# Purpose: Limits token usage during health check (keeps it fast and cheap)
# Default: 10
# Example: MISTRAL_STARTUP_MAX_TOKENS=10

MISTRAL_MAX_RETRIES=3
# Description: Number of retry attempts for failed API calls
# Purpose: How many times to retry failed Mistral API requests
# Default: 3
# Use cases:
#   - Network instability: Increase retries
#   - Stable network: Decrease to fail faster
# Example: MISTRAL_MAX_RETRIES=5

MISTRAL_EMBEDDING_BATCH_SIZE_SMALL=5
# Description: Batch size for embedding large document sets
# Purpose: How many text chunks to embed in one API call for large sets
# Default: 5
# Trade-off: Smaller batches = more reliable but slower
# Example: MISTRAL_EMBEDDING_BATCH_SIZE_SMALL=3

MISTRAL_EMBEDDING_BATCH_SIZE_LARGE=10
# Description: Batch size for embedding small document sets
# Purpose: How many text chunks to embed in one API call for small sets
# Default: 10
# Trade-off: Larger batches = faster but may timeout
# Example: MISTRAL_EMBEDDING_BATCH_SIZE_LARGE=15

MISTRAL_EMBEDDING_BATCH_THRESHOLD=50
# Description: Threshold to switch between small/large batch sizes
# Purpose: Number of chunks that determines batch strategy
# Default: 50
# Logic: If chunks > 50, use SMALL batch size; else use LARGE
# Example: MISTRAL_EMBEDDING_BATCH_THRESHOLD=100
```

#### Weather API Configuration

```env
OPENWEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather
# Description: OpenWeatherMap API endpoint
# Purpose: URL for fetching weather data
# Default: https://api.openweathermap.org/data/2.5/weather
# Example: OPENWEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather

OPENWEATHER_API_TIMEOUT=30.0
# Description: Timeout for weather API requests (seconds)
# Purpose: How long to wait for weather data before timeout
# Default: 30.0 seconds
# Example: OPENWEATHER_API_TIMEOUT=45.0
```

#### RAG (Document Search) Configuration

```env
RAG_MAX_CONTEXT_CHUNKS=5
# Description: Maximum number of document chunks to retrieve
# Purpose: How many relevant text chunks to include in RAG context
# Default: 5
# Trade-off:
#   - More chunks: Better context but slower and uses more tokens
#   - Fewer chunks: Faster but may miss relevant information
# Typical values:
#   - 3-5: Fast, focused answers
#   - 5-10: Comprehensive answers
#   - 10+: Deep research (may hit token limits)
# Example: RAG_MAX_CONTEXT_CHUNKS=10

RAG_MAX_CONTEXT_LENGTH=2000
# Description: Maximum total character length of retrieved context
# Purpose: Limits combined length of all retrieved chunks
# Default: 2000 characters
# Trade-off: Higher = more context but uses more tokens
# Example: RAG_MAX_CONTEXT_LENGTH=3000

RAG_CHUNK_SIZE=500
# Description: Size of text chunks for document splitting
# Purpose: How large each text chunk is when splitting documents
# Default: 500 characters
# Trade-off:
#   - Smaller chunks (200-300): More precise, granular search
#   - Medium chunks (500-800): Balanced (recommended)
#   - Larger chunks (1000+): More context per chunk but less precise
# Example: RAG_CHUNK_SIZE=800

RAG_CHUNK_OVERLAP=50
# Description: Overlap between consecutive chunks
# Purpose: How many characters overlap between adjacent chunks
# Default: 50 characters
# Why needed: Prevents splitting sentences/paragraphs awkwardly
# Typical values:
#   - 10-20% of chunk size
#   - 50-100 characters for 500-char chunks
# Example: RAG_CHUNK_OVERLAP=100
```

#### Document Upload Configuration

```env
MAX_UPLOAD_SIZE_MB=10
# Description: Maximum file upload size in megabytes
# Purpose: Limits size of documents users can upload
# Default: 10 MB
# Considerations:
#   - Larger files take longer to process
#   - Larger files generate more embeddings (costs money)
#   - Adjust based on your use case and budget
# Example: MAX_UPLOAD_SIZE_MB=50
```

#### Network Configuration

```env
SOCKET_TIMEOUT=1.0
# Description: Socket timeout for port checking (seconds)
# Purpose: How long startup check waits to test if port is available
# Default: 1.0 second
# Example: SOCKET_TIMEOUT=2.0
```

#### Logging Configuration

```env
DEBUG_THIRD_PARTY=false
# Description: Enable debug logging for third-party libraries
# Purpose: Shows detailed logs from libraries (httpx, motor, etc.)
# Default: false
# Options: true (verbose), false (clean)
# Use case: Debugging library-related issues
# Example: DEBUG_THIRD_PARTY=true

MINIMAL_LOGGING=true
# Description: Use minimal logging (less verbose)
# Purpose: Reduces log verbosity for cleaner output
# Default: true
# Options: true (clean), false (detailed)
# Example: MINIMAL_LOGGING=false
```

#### Orchestrator Configuration

```env
STRICT_TOOL_MATCHING=true
# Description: Require exact tool matches (prevents hallucination)
# Purpose: Controls whether LLM can answer questions outside tool scope
# Default: true (recommended for production)
# Options:
#   - true: LLM must select a tool or return "I don't know"
#   - false: LLM can answer general questions (may hallucinate)
# Example: STRICT_TOOL_MATCHING=false
```

#### Token Estimation Configuration

```env
CHARS_PER_TOKEN=4
# Description: Estimated characters per token
# Purpose: Used to estimate token count from text length
# Default: 4 (standard estimate for English text)
# Note: Actual ratio varies by language and tokenizer
# Example: CHARS_PER_TOKEN=4
```

---

### Configuration Summary Table

| Category | Variable | Default | Impact |
|----------|----------|---------|--------|
| **Server** | PORT | 8011 | Network access |
| **Server** | HOST | 127.0.0.1 | Access scope |
| **LLM** | MISTRAL_TEMPERATURE | 0.7 | Response creativity |
| **LLM** | MISTRAL_MAX_TOKENS | 500 | Response length |
| **LLM** | MISTRAL_MODEL | mistral-small-2503 | Quality/cost/speed |
| **RAG** | RAG_CHUNK_SIZE | 500 | Search precision |
| **RAG** | RAG_MAX_CONTEXT_CHUNKS | 5 | Context quality |
| **Upload** | MAX_UPLOAD_SIZE_MB | 10 | File size limit |
| **Database** | DATABASE_TIMEOUT_MS | 5000 | Connection reliability |

---

# Upload Configuration
MAX_UPLOAD_SIZE_MB=10
# Maximum file upload size in MB (default: 10)
```

---

## 📖 Usage

### Starting the Backend Server

```bash
python main.py
```

The server will start on `http://127.0.0.1:8011`

### Accessing the API

- **API Root**: http://127.0.0.1:8011
- **Interactive API Documentation (Swagger)**: http://127.0.0.1:8011/docs
- **Alternative API Documentation (ReDoc)**: http://127.0.0.1:8011/redoc
- **Health Check**: http://127.0.0.1:8011/health

### Using the API

#### 1. Create a User
```bash
curl -X POST "http://127.0.0.1:8011/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'
```

#### 2. Upload a Document
```bash
curl -X POST "http://127.0.0.1:8011/documents/upload" \
  -F "file=@document.pdf" \
  -F "user_id=USER_ID_HERE"
```

#### 3. Ask a Question (Weather)
```bash
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID_HERE",
    "user_input": "What is the weather in Paris?"
  }'
```

#### 4. Ask a Question (Document Search)
```bash
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID_HERE",
    "user_input": "Find information about shipping rates"
  }'
```

### Expected Behavior

| User Question | Tool Selected | Response |
|--------------|---------------|----------|
| "What's the weather in Tokyo?" | `weather_query` | Weather data from OpenWeatherMap |
| "Search my documents for contracts" | `rag_search` | Relevant document excerpts |
| "What is 2+2?" | `none` | "I don't know - I can only help with weather and documents" |
| "Tell me a joke" | `none` | "I don't know - I can only help with weather and documents" |

---

## 📚 API Documentation

### Main Endpoints

#### Orchestrator (Main Chat Interface)
- **POST** `/orchestrator/chat` - Send message to bot (intelligent tool selection)

#### Users
- **POST** `/users/` - Create new user
- **GET** `/users/{user_id}` - Get user by ID
- **GET** `/users/` - List all users

#### Documents
- **POST** `/documents/upload` - Upload document for RAG search
- **POST** `/documents/query` - Query documents directly
- **GET** `/documents/user/{user_id}` - List user's documents
- **DELETE** `/documents/{document_id}` - Delete document

#### Messages
- **POST** `/messages/` - Create message
- **GET** `/messages/user/{user_id}` - Get user's messages
- **GET** `/messages/conversation/{conversation_id}` - Get conversation messages

#### Basic
- **GET** `/` - Root endpoint
- **GET** `/health` - Health check

### Interactive API Documentation

Visit `http://127.0.0.1:8011/docs` for interactive Swagger UI where you can:
- Test all endpoints
- See request/response schemas
- Execute API calls directly from browser

---

## 🗂️ Project Structure

```
backend/
├── main.py                    # Application entry point
├── startup.py                 # Startup health checks
├── data_validation.py         # Pydantic models
├── requirements.txt           # Backend dependencies
├── prompts.txt               # ⭐ All LLM prompts
├── .env                       # Environment variables (create this)
│
├── core/                      # Core business logic
│   ├── config.py             # ⚙️ Configuration settings
│   ├── prompt_loader.py      # 📝 Loads prompts from prompts.txt
│   ├── orchestrator.py       # 🎯 Main orchestration logic
│   ├── mistral_service.py    # 🤖 Mistral AI API integration
│   ├── embedding_service.py  # 🔢 Embedding generation
│   ├── rag_service.py        # 📄 RAG document search
│   ├── rag_utils.py          # 🔧 RAG utilities
│   ├── document_processor.py # 📎 Document processing
│   ├── logger.py             # 📊 Custom logging
│   └── crud.py               # 💾 Database operations
│
│   └── bot_tools/            # Modular bot tools
│       ├── base_tool.py      # Base class for tools
│       ├── weather_tool.py   # 🌤️ Weather tool
│       └── rag_tool.py       # 📚 RAG tool
│
├── database/                  # Database adapters
│   ├── interface.py          # Database interface
│   ├── factory.py            # Database factory
│   └── mongodb_adapter.py    # MongoDB implementation
│
├── routes/                    # API endpoints
│   ├── orchestrator.py       # Orchestrator endpoints
│   ├── documents.py          # Document endpoints
│   ├── users.py              # User endpoints
│   ├── messages.py           # Message endpoints
│   └── basic.py              # Basic endpoints
│
├── logs/                      # Log files
│   ├── debug.txt
│   ├── error.txt
│   ├── prompt.txt
│   └── timing.txt
│
└── vector_storage/            # Vector database storage
```

---

## 📝 Prompt Management

All LLM prompts are stored in `prompts.txt` for easy editing without code changes.

### Prompt Structure

```txt
[main_prompt]
# Tool selection prompt
# Used by orchestrator to choose which tool to use

[tool_weather_response]
# Weather response formatting prompt
# Used to format weather data into user-friendly response

[tool_rag_response]
# RAG response formatting prompt
# Used to format document search results
```

### Editing Prompts

1. Open `prompts.txt`
2. Edit the prompt text
3. Save the file
4. Restart the application

**No code changes needed!**

### Variables in Prompts

Prompts support variable substitution:
- `{user_input}` - User's question
- `{user_query}` - User's query
- `{weather_data}` - Weather API response
- `{rag_data}` - Document search results

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```
Error: Port 8011 is already in use
```
**Solution:** Change the port in `.env`:
```env
PORT=8012
```

#### 2. MongoDB Connection Failed
```
Error: Cannot connect to MongoDB
```
**Solutions:**
- Ensure MongoDB is running: `net start MongoDB` (Windows) or `brew services start mongodb-community` (Mac)
- Check connection string in `.env`
- Verify MongoDB is installed

#### 3. Mistral API Key Invalid
```
Error: Mistral API authentication failed
```
**Solution:**
- Verify API key is correct in `.env`
- Check key has no extra spaces
- Ensure key is active at https://console.mistral.ai/

#### 4. Import Errors
```
ModuleNotFoundError: No module named 'xyz'
```
**Solution:**
```bash
pip install -r requirements.txt
```

#### 5. Virtual Environment Not Activated
```
Error: Commands not working as expected
```
**Solution:** Activate virtual environment:
```bash
# Windows
..\myvenv\Scripts\Activate.ps1

# Mac/Linux
source ../myvenv/bin/activate
```

#### 6. Document Upload Fails
```
Error: File size too large
```
**Solution:** Increase upload limit in `.env`:
```env
MAX_UPLOAD_SIZE_MB=20
```

### Checking Logs

Logs are stored in `logs/`:
- `debug.txt` - Debug information
- `error.txt` - Error messages
- `prompt.txt` - All LLM prompts and responses
- `timing.txt` - Performance timing data

---

## 🧪 Testing

### Health Check
```bash
curl http://127.0.0.1:8011/health
```

### Test Tool Selection
```bash
# Should select weather_query
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_input": "Weather in London"}'

# Should select rag_search
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_input": "Search documents for pricing"}'

# Should return "I don't know"
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_input": "What is 2+2?"}'
```

### Test Individual Endpoints

Visit `http://127.0.0.1:8011/docs` to test all endpoints interactively.

---

## 📊 Key Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MISTRAL_TEMPERATURE` | 0.7 | Response creativity (0.0=factual, 1.0=creative) |
| `MISTRAL_MAX_TOKENS` | 500 | Maximum response length |
| `RAG_MAX_CONTEXT_CHUNKS` | 5 | Documents chunks to retrieve |
| `RAG_CHUNK_SIZE` | 500 | Text chunk size for splitting |
| `MAX_UPLOAD_SIZE_MB` | 10 | Maximum file upload size |

**See `.env` file comments for detailed descriptions of all 30+ configuration variables.**

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Mohamadaliibrahim/fastapi_mini_project/issues)
- **Mistral AI Docs**: https://docs.mistral.ai/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

## 📄 License

This project is licensed under the MIT License.
