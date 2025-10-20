# FastAPI Mini Project - Intelligent Bot Backend

A production-ready FastAPI backend with intelligent orchestration, RAG (Retrieval-Augmented Generation) document search, weather queries, and LLM-powered tool selection using Mistral AI.

## 📋 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Prompt Management](#prompt-management)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Introduction

This FastAPI application provides an intelligent bot system that:
- Uses LLM (Large Language Model) to intelligently select appropriate tools
- Searches documents using RAG (Retrieval-Augmented Generation)
- Provides weather information for any location worldwide
- Prevents hallucination by restricting responses to available tools
- Manages all prompts centrally in a configuration file
- Includes comprehensive logging and error handling

---

## ✨ Features

### Core Functionality
- **🤖 Intelligent Tool Selection**: LLM-powered orchestrator that selects the right tool based on user intent
- **📄 Document Search (RAG)**: Semantic search through uploaded documents with embedding-based retrieval
- **🌤️ Weather Queries**: Real-time weather information using OpenWeatherMap API
- **🚫 Anti-Hallucination**: Strict tool matching prevents AI from generating responses outside its capabilities
- **📝 Centralized Prompt Management**: All LLM prompts stored in `prompts.txt` for easy editing
- **🔧 Configuration Management**: Zero hardcoded values - all settings in `config.py` and environment variables
- **📊 Comprehensive Logging**: Detailed logging for debugging, errors, and prompt tracking
- **🗄️ MongoDB Integration**: Persistent storage for users, messages, and conversations
- **⚡ Async Processing**: High-performance async/await architecture

### Technical Features
- FastAPI framework with automatic OpenAPI documentation
- Vector embeddings using Mistral AI
- Chromadb for vector storage
- CORS support for frontend integration
- Startup health checks for all services
- Streamlit frontend for testing

---

## 🏗️ Architecture

```
User Request
    ↓
Orchestrator (LLM selects tool)
    ↓
    ├─ Weather Tool → OpenWeatherMap API
    ├─ RAG Tool → Vector DB → Document Search
    └─ None → "I don't know" response
    ↓
LLM Formats Response
    ↓
User Receives Answer
```

### Key Components
1. **Orchestrator**: Routes requests to appropriate tools using LLM intelligence
2. **Bot Tools**: Modular tools (Weather, RAG) that execute specific tasks
3. **RAG Service**: Handles document processing, embedding, and semantic search
4. **Mistral Service**: Manages all LLM API calls
5. **Prompt Loader**: Loads and manages prompts from `prompts.txt`

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** (Python 3.12 is recommended)
- **MongoDB** (local installation or MongoDB Atlas account)
- **Git** (for cloning the repository)
- **pip** (Python package installer)
- **API Keys**:
  - Mistral AI API Key ([Get it here](https://console.mistral.ai/))
  - OpenWeatherMap API Key ([Get it here](https://openweathermap.org/api))

### System Requirements
- Operating System: Windows, macOS, or Linux
- RAM: Minimum 4GB (8GB recommended)
- Disk Space: 1GB free space

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
```

### Step 2: Navigate to Project Directory

```bash
cd fastapi_mini_project
```

### Step 3: Create Virtual Environment

**On Windows:**
```powershell
python -m venv myvenv
```

**On macOS/Linux:**
```bash
python3 -m venv myvenv
```

### Step 4: Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
.\myvenv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
myvenv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
source myvenv/bin/activate
```

### Step 5: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 6: Install Frontend Dependencies (Optional)

```bash
cd ../frontend
pip install -r requirements.txt
```

### Step 7: Set Up Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cd ../backend
```

**On Windows:**
```powershell
New-Item .env -ItemType File
```

**On macOS/Linux:**
```bash
touch .env
```

Edit the `.env` file and add your configuration (see [Environment Variables](#environment-variables) section below).

### Step 8: Start MongoDB

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

### Step 9: Run the Application

**Backend (FastAPI):**
```bash
cd backend
python main.py
```

The backend will start on `http://127.0.0.1:8011`

**Frontend (Streamlit) - In a new terminal:**
```bash
cd frontend
streamlit run main.py
```

The frontend will start on `http://localhost:8501`

---

## ⚙️ Configuration

All configuration is centralized in `backend/core/config.py`. You can override any setting using environment variables.

### Key Configuration Files

1. **`backend/core/config.py`**: Main configuration class
2. **`backend/.env`**: Environment variables (create this file)
3. **`backend/prompts.txt`**: All LLM prompts
4. **`backend/requirements.txt`**: Python dependencies

---

## 🔐 Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

### Required Variables

```env
# ============================================
# REQUIRED - Application will not work without these
# ============================================

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here
# Description: Your Mistral AI API key for LLM calls
# Get it from: https://console.mistral.ai/
# Example: MISTRAL_API_KEY=abc123xyz456

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
# Description: MongoDB connection string
# Local: mongodb://localhost:27017
# Atlas: mongodb+srv://username:password@cluster.mongodb.net/

DATABASE_NAME=bot_database
# Description: Name of the MongoDB database
# Default: bot_database
# You can change this to any name you prefer

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_openweather_api_key_here
# Description: API key for weather data
# Get it from: https://openweathermap.org/api
# Free tier available with 1000 calls/day
```

### Optional Variables (with defaults)

```env
# ============================================
# SERVER CONFIGURATION
# ============================================

HOST=127.0.0.1
# Description: Server host address
# Default: 127.0.0.1 (localhost)
# Use 0.0.0.0 to allow external access

PORT=8011
# Description: Server port number
# Default: 8011
# Change if port is already in use

RELOAD=true
# Description: Auto-reload server on code changes
# Default: true
# Set to false in production

LOG_LEVEL=info
# Description: Logging level (debug, info, warning, error)
# Default: info
# Use debug for detailed logs

# ============================================
# DATABASE CONFIGURATION
# ============================================

DATABASE_TYPE=mongodb
# Description: Type of database (currently only mongodb supported)
# Default: mongodb

DATABASE_TIMEOUT_MS=5000
# Description: Database connection timeout in milliseconds
# Default: 5000 (5 seconds)

# ============================================
# MISTRAL AI CONFIGURATION
# ============================================

MISTRAL_MODEL=mistral-small-2503
# Description: Mistral AI model to use
# Default: mistral-small-2503
# Other options: mistral-medium, mistral-large

MISTRAL_EMBEDDING_MODEL=codestral-embed
# Description: Model for generating embeddings
# Default: codestral-embed

MISTRAL_TEMPERATURE=0.7
# Description: LLM temperature (0.0-1.0, higher = more creative)
# Default: 0.7
# Lower for factual responses, higher for creative

MISTRAL_MAX_TOKENS=500
# Description: Maximum tokens in LLM response
# Default: 500
# Increase for longer responses

MISTRAL_MAX_CONTEXT_TOKENS=10000
# Description: Maximum tokens in conversation context
# Default: 10000

MISTRAL_API_TIMEOUT=60.0
# Description: Timeout for Mistral API calls (seconds)
# Default: 60.0

MISTRAL_EMBEDDING_TIMEOUT=120.0
# Description: Timeout for embedding generation (seconds)
# Default: 120.0 (embeddings take longer)

MISTRAL_MAX_RETRIES=3
# Description: Number of retries for failed API calls
# Default: 3

MISTRAL_EMBEDDING_BATCH_SIZE_SMALL=5
# Description: Batch size for embedding large document sets
# Default: 5

MISTRAL_EMBEDDING_BATCH_SIZE_LARGE=10
# Description: Batch size for embedding small document sets
# Default: 10

MISTRAL_EMBEDDING_BATCH_THRESHOLD=50
# Description: Threshold to switch between small/large batch sizes
# Default: 50

MISTRAL_STARTUP_TIMEOUT=10.0
# Description: Timeout for startup health check (seconds)
# Default: 10.0

MISTRAL_STARTUP_MAX_TOKENS=10
# Description: Max tokens for startup test
# Default: 10

# ============================================
# RAG (Document Search) CONFIGURATION
# ============================================

RAG_MAX_CONTEXT_CHUNKS=5
# Description: Maximum number of document chunks to retrieve
# Default: 5
# Increase for more context, decrease for speed

RAG_MAX_CONTEXT_LENGTH=2000
# Description: Maximum total length of retrieved context
# Default: 2000 characters

RAG_CHUNK_SIZE=500
# Description: Size of text chunks for document splitting
# Default: 500 characters
# Smaller = more precise, larger = more context

RAG_CHUNK_OVERLAP=50
# Description: Overlap between consecutive chunks
# Default: 50 characters
# Helps maintain context across chunk boundaries

# ============================================
# DOCUMENT UPLOAD CONFIGURATION
# ============================================

MAX_UPLOAD_SIZE_MB=10
# Description: Maximum file upload size in megabytes
# Default: 10 MB
# Increase for larger documents

# ============================================
# WEATHER API CONFIGURATION
# ============================================

OPENWEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather
# Description: OpenWeatherMap API endpoint
# Default: https://api.openweathermap.org/data/2.5/weather
# Usually no need to change

OPENWEATHER_API_TIMEOUT=30.0
# Description: Timeout for weather API calls (seconds)
# Default: 30.0

# ============================================
# NETWORK CONFIGURATION
# ============================================

SOCKET_TIMEOUT=1.0
# Description: Socket timeout for port checking (seconds)
# Default: 1.0

# ============================================
# LOGGING CONFIGURATION
# ============================================

DEBUG_THIRD_PARTY=false
# Description: Enable debug logging for third-party libraries
# Default: false
# Set to true to see all library logs

MINIMAL_LOGGING=true
# Description: Use minimal logging (less verbose)
# Default: true
# Set to false for detailed logs

# ============================================
# ORCHESTRATOR CONFIGURATION
# ============================================

STRICT_TOOL_MATCHING=true
# Description: Require exact tool matches (prevents hallucination)
# Default: true
# Set to false to allow LLM to answer general questions
```

### Example `.env` File

```env
# Minimum required configuration
MISTRAL_API_KEY=sk-abc123xyz456def789
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=bot_database
OPENWEATHER_API_KEY=1234567890abcdef

# Optional overrides
PORT=8011
MISTRAL_TEMPERATURE=0.5
RAG_MAX_CONTEXT_CHUNKS=10
LOG_LEVEL=debug
```

---

## 📖 Usage

### Starting the Application

1. **Start Backend:**
```bash
cd backend
python main.py
```

2. **Start Frontend (optional):**
```bash
cd frontend
streamlit run main.py
```

### Accessing the Application

- **Backend API**: http://127.0.0.1:8011
- **API Documentation**: http://127.0.0.1:8011/docs (Swagger UI)
- **Alternative API Docs**: http://127.0.0.1:8011/redoc (ReDoc)
- **Frontend UI**: http://localhost:8501

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
fastapi_mini_project/
├── backend/
│   ├── main.py                    # Application entry point
│   ├── startup.py                 # Startup health checks
│   ├── data_validation.py         # Pydantic models
│   ├── requirements.txt           # Backend dependencies
│   ├── prompts.txt               # ⭐ All LLM prompts
│   ├── .env                       # Environment variables (create this)
│   │
│   ├── core/                      # Core business logic
│   │   ├── config.py             # ⚙️ Configuration settings
│   │   ├── prompt_loader.py      # 📝 Loads prompts from prompts.txt
│   │   ├── orchestrator.py       # 🎯 Main orchestration logic
│   │   ├── mistral_service.py    # 🤖 Mistral AI API integration
│   │   ├── embedding_service.py  # 🔢 Embedding generation
│   │   ├── rag_service.py        # 📄 RAG document search
│   │   ├── rag_utils.py          # 🔧 RAG utilities
│   │   ├── document_processor.py # 📎 Document processing
│   │   ├── logger.py             # 📊 Custom logging
│   │   └── crud.py               # 💾 Database operations
│   │
│   │   └── bot_tools/            # Modular bot tools
│   │       ├── base_tool.py      # Base class for tools
│   │       ├── weather_tool.py   # 🌤️ Weather tool
│   │       └── rag_tool.py       # 📚 RAG tool
│   │
│   ├── database/                  # Database adapters
│   │   ├── interface.py          # Database interface
│   │   ├── factory.py            # Database factory
│   │   └── mongodb_adapter.py    # MongoDB implementation
│   │
│   ├── routes/                    # API endpoints
│   │   ├── orchestrator.py       # Orchestrator endpoints
│   │   ├── documents.py          # Document endpoints
│   │   ├── users.py              # User endpoints
│   │   ├── messages.py           # Message endpoints
│   │   └── basic.py              # Basic endpoints
│   │
│   ├── logs/                      # Log files
│   │   ├── debug.txt
│   │   ├── error.txt
│   │   ├── prompt.txt
│   │   └── timing.txt
│   │
│   └── vector_storage/            # Vector database storage
│
├── frontend/                      # Streamlit frontend
│   ├── main.py                   # Frontend entry point
│   ├── api_client.py             # Backend API client
│   ├── config.py                 # Frontend config
│   ├── utils.py                  # Frontend utilities
│   └── requirements.txt          # Frontend dependencies
│
├── myvenv/                        # Virtual environment (created)
├── README.md                      # This file
└── QUICK_START.md                # Quick start guide
```

---

## 📝 Prompt Management

All LLM prompts are stored in `backend/prompts.txt` for easy editing without code changes.

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

1. Open `backend/prompts.txt`
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
.\myvenv\Scripts\Activate.ps1

# Mac/Linux
source myvenv/bin/activate
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

Logs are stored in `backend/logs/`:
- `debug.txt` - Debug information
- `error.txt` - Error messages
- `prompt.txt` - All LLM prompts and responses
- `timing.txt` - Performance timing data

### Getting Help

If you encounter issues:
1. Check logs in `backend/logs/`
2. Verify all environment variables are set
3. Ensure all services (MongoDB, APIs) are running
4. Check API documentation at http://127.0.0.1:8011/docs

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

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature-name`
6. Create a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to functions
- Update prompts.txt for new prompts
- Test all changes before submitting
- Update README if adding new features

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Authors

- **Mohamad Ali Ibrahim** - [GitHub](https://github.com/Mohamadaliibrahim)

---

## 🙏 Acknowledgments

- **Mistral AI** - LLM and embeddings
- **OpenWeatherMap** - Weather data
- **FastAPI** - Web framework
- **MongoDB** - Database
- **Chromadb** - Vector storage
- **Streamlit** - Frontend framework

---

## 📞 Support

For support:
- Open an issue on GitHub
- Check the [API Documentation](http://127.0.0.1:8011/docs)
- Review logs in `backend/logs/`

---

**Happy Coding! 🚀**
