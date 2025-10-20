# FastAPI Backend - Intelligent Bot API

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
- [Testing](#testing)

---

## 🎯 Introduction

This FastAPI backend provides an intelligent bot system that:
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
1. **Orchestrator** (`core/orchestrator.py`): Routes requests to appropriate tools using LLM intelligence
2. **Bot Tools** (`core/bot_tools/`): Modular tools (Weather, RAG) that execute specific tasks
3. **RAG Service** (`core/rag_service.py`): Handles document processing, embedding, and semantic search
4. **Mistral Service** (`core/mistral_service.py`): Manages all LLM API calls
5. **Prompt Loader** (`core/prompt_loader.py`): Loads and manages prompts from `prompts.txt`

---

## 📦 Prerequisites

Before you begin, ensure you have the following:

- **Python 3.12+** (Python 3.12 is recommended)
- **MongoDB** (local installation or MongoDB Atlas account)
- **pip** (Python package installer)
- **API Keys**:
  - Mistral AI API Key ([Get it here](https://console.mistral.ai/))
  - OpenWeatherMap API Key ([Get it here](https://openweathermap.org/api))

### System Requirements
- Operating System: Windows, macOS, or Linux
- RAM: Minimum 4GB (8GB recommended)
- Disk Space: 500MB free space

---

## 🚀 Installation

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Virtual Environment (if not already created)

**On Windows:**
```powershell
python -m venv ../myvenv
```

**On macOS/Linux:**
```bash
python3 -m venv ../myvenv
```

### Step 3: Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
..\myvenv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
..\myvenv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
source ../myvenv/bin/activate
```

### Step 4: Install Backend Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Motor** - Async MongoDB driver
- **Mistral AI SDK** - LLM integration
- **Chromadb** - Vector database
- **LangChain** - Document processing
- **httpx** - HTTP client
- **python-dotenv** - Environment variable management
- And more...

### Step 5: Set Up Environment Variables

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

Add your configuration (see [Environment Variables](#environment-variables) section below).

### Step 6: Start MongoDB

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

```env
# ============================================
# REQUIRED CONFIGURATION
# ============================================

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here
# Your Mistral AI API key for LLM calls
# Get it from: https://console.mistral.ai/

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
# MongoDB connection string
# For local: mongodb://localhost:27017
# For Atlas: mongodb+srv://username:password@cluster.mongodb.net/

DATABASE_NAME=bot_database
# Name of the MongoDB database

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_openweather_api_key_here
# API key for weather data
# Get it from: https://openweathermap.org/api

# ============================================
# OPTIONAL CONFIGURATION (with defaults)
# ============================================

# Server Configuration
PORT=8011
# Server port number (default: 8011)

HOST=127.0.0.1
# Server host (default: 127.0.0.1)

# Mistral AI Model Settings
MISTRAL_MODEL=mistral-small-2503
# AI model to use (default: mistral-small-2503)

MISTRAL_TEMPERATURE=0.7
# LLM temperature 0.0-1.0 (default: 0.7)

MISTRAL_MAX_TOKENS=500
# Maximum tokens in response (default: 500)

# RAG Configuration
RAG_MAX_CONTEXT_CHUNKS=5
# Maximum document chunks to retrieve (default: 5)

RAG_CHUNK_SIZE=500
# Size of text chunks (default: 500)

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
