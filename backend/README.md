# Assistant Chatbot 



FastAPI-based intelligent chatbot backend with LLM-powered orchestration, RAG document search, and weather query capabilities.FastAPI intelligent chatbot backend with LLM orchestration, RAG document search, and weather queries.



## Table of Contents# Description



- [Introduction](#introduction)Intelligent assistant backend using Mistral AI to route queries to appropriate tools:

- [Features](#features)- **Weather Tool**: Real-time weather via OpenWeatherMap

- [Prerequisites](#prerequisites)- **RAG Tool**: Semantic document search with vector embeddings

- [Installation](#installation)- **Anti-Hallucination**: Returns "I don't know" for out-of-scope queries

- [Configuration](#configuration)

- [Environment Variables](#environment-variables)## Installation

- [Usage](#usage)

- [API Documentation](#api-documentation)**Requirements:** Python 3.12+, MongoDB, API Keys ([Mistral AI](https://console.mistral.ai/), [OpenWeatherMap](https://openweathermap.org/api))

- [Manual Deployment](#manual-deployment)

```markdown
Quick clone (copy & paste):

```powershell
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project\backend
```

Then follow the Installation section below to create a virtualenv, install dependencies and run the server.

What this project does (short):
- FastAPI backend that routes queries to tools (RAG document search, weather) using an LLM orchestrator.

Run the server: `python startup.py` (after setup)

---

## Configuration

## Features

**Required:**

- **🤖 Intelligent Tool Selection**: LLM automatically determines which tool to use based on user intent```env

- **📄 RAG Document Search**: Upload documents and search through them using semantic vector embeddingsMISTRAL_API_KEY, MONGODB_URL, DATABASE_NAME, OPENWEATHER_API_KEY

- **🌤️ Weather Queries**: Get real-time weather information for any location worldwide```

- **🚫 Anti-Hallucination**: System returns "I don't know" for queries outside its tool scope

- **📝 Centralized Prompt Management**: All LLM prompts stored in `prompts.txt` for easy editing**Optional (defaults):**

- **⚙️ Zero Hardcoding**: All configurations managed through environment variables```env

- **📊 Comprehensive Logging**: Detailed logs for debugging, errors, and LLM interactionsPORT=8011, MISTRAL_TEMPERATURE=0.7, MISTRAL_MAX_TOKENS=500, RAG_CHUNK_SIZE=500

- **🗄️ MongoDB Integration**: Persistent storage for users, messages, and conversations```

- **⚡ Async Processing**: High-performance async/await architecture with FastAPI

## Project Structure

---

```

## Prerequisitesbackend/

 startup.py, main.py, prompts.txt

Before setting up the project, ensure you have the following: core/ (orchestrator.py, mistral_service.py, rag_service.py, bot_tools/)

 database/ (mongodb_adapter.py)

### Required Software routes/ (users.py, documents.py, messages.py)

- **Python 3.12 or higher**: [Download Python](https://www.python.org/downloads/) logs/

- **MongoDB**: Either local installation or MongoDB Atlas account```

  - Local: [Download MongoDB Community Server](https://www.mongodb.com/try/download/community)

  - Cloud: [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)## Troubleshooting

- **Git**: For cloning the repository

- **pip**: Python package manager (comes with Python)- **Port in use:** Change `PORT` in `.env`

- **MongoDB failed:** `net start MongoDB` (Windows) or `brew services start mongodb-community` (Mac)

### Required API Keys- **Module not found:** `pip install -r requirements.txt`

1. **Mistral AI API Key**- **Check logs:** `logs/error.txt`, `logs/debug.txt`

   - Sign up at [console.mistral.ai](https://console.mistral.ai/)

   - Navigate to API Keys section## License

   - Create a new API key

   - Copy and save it securelyMIT License - Copyright (c) 2025 Mohamad Ali Ibrahim


2. **OpenWeatherMap API Key**
   - Sign up at [openweathermap.org](https://openweathermap.org/api)
   - Free tier is sufficient for development
   - Navigate to API Keys section
   - Copy your API key

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 500MB free space
- **Internet Connection**: Required for API calls and package installation

---

## Installation

Follow these step-by-step instructions to set up the project locally.

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
```

**What this does:** Downloads the entire project codebase to your local machine.

### Step 2: Navigate to the Backend Directory

```bash
cd fastapi_mini_project/backend
```

**What this does:** Changes your current directory to the backend folder where all backend code resides.

### Step 3: Create a Virtual Environment

**On Windows:**
```powershell
python -m venv ..\myvenv
```

**On macOS/Linux:**
```bash
python3 -m venv ../myvenv
```

**What this does:** Creates an isolated Python environment called `myvenv` in the parent directory. This keeps project dependencies separate from your system Python installation.

### Step 4: Activate the Virtual Environment

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

**What this does:** Activates the virtual environment. You'll see `(myvenv)` prefix in your terminal prompt, indicating the environment is active.

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

**What this does:** Installs all required Python packages listed in `requirements.txt`, including:
- **FastAPI**: Web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Motor**: Async MongoDB driver
- **Mistralai**: Mistral AI SDK for LLM integration
- **Chromadb**: Vector database for embeddings
- **LangChain**: Document processing and text splitting
- **httpx**: HTTP client for API requests
- **python-dotenv**: Environment variable management
- And many more dependencies...

### Step 6: Set Up MongoDB

Ensure MongoDB is running on your system.

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

**What this does:** Starts the MongoDB service so the application can connect to the database.

### Step 7: Configure Environment Variables

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

Then add your configuration (see [Environment Variables](#environment-variables) section below).

**What this does:** Creates a configuration file where you'll store all your API keys and settings. This file is not committed to Git for security.

### Step 8: Run the Application

```bash
python startup.py
```

**What this does:** Starts the FastAPI backend server. The application will:
- Load configuration from `.env` file
- Connect to MongoDB
- Verify Mistral AI API connectivity
- Start the server on the configured port (default: 8011)

**Access the application:**
- **API Server**: http://127.0.0.1:8011
- **API Documentation**: http://127.0.0.1:8011/docs
- **Alternative Docs**: http://127.0.0.1:8011/redoc

---

## Configuration

All configuration is centralized in `core/config.py` and can be overridden using environment variables in the `.env` file.

### Configuration Files

1. **`core/config.py`**: Main configuration class with all settings and defaults
2. **`.env`**: Environment variables file (you create this)
3. **`prompts.txt`**: All LLM prompts for tool selection and response formatting
4. **`requirements.txt`**: Python dependencies list

---

## Environment Variables

Create a `.env` file in the `backend` directory with the following variables. Each variable is explained in detail below.

### Required Variables

These variables **must** be set for the application to function:

```env
# Mistral AI API Key
MISTRAL_API_KEY=your_mistral_api_key_here
```
**What it is:** Your authentication key for Mistral AI API  
**Where to get it:** [console.mistral.ai](https://console.mistral.ai/)  
**What it does:** Authenticates all requests to Mistral AI for chat completions and embeddings  
**Example:** `MISTRAL_API_KEY=sk-abc123def456ghi789`

```env
# MongoDB Connection String
MONGODB_URL=mongodb://localhost:27017
```
**What it is:** Database connection string  
**Where to get it:** 
- Local: Use `mongodb://localhost:27017`
- Atlas: Get from MongoDB Atlas dashboard  
**What it does:** Connects the application to MongoDB for storing users, messages, and conversations  
**Examples:**
- Local: `mongodb://localhost:27017`
- Atlas: `mongodb+srv://username:password@cluster.mongodb.net/`

```env
# Database Name
DATABASE_NAME=bot_database
```
**What it is:** Name of the MongoDB database to use  
**What it does:** Specifies which database within MongoDB stores application data  
**Default:** `bot_database`  
**Example:** `DATABASE_NAME=my_chatbot_db`

```env
# OpenWeatherMap API Key
OPENWEATHER_API_KEY=your_openweather_api_key_here
```
**What it is:** API key for accessing weather data  
**Where to get it:** [openweathermap.org/api](https://openweathermap.org/api)  
**What it does:** Enables the weather tool to fetch real-time weather information  
**Example:** `OPENWEATHER_API_KEY=1234567890abcdef`

---

### Optional Variables (Advanced Configuration)

These variables have default values but can be customized:

#### Server Configuration

```env
HOST=127.0.0.1
```
**What it is:** Server host address  
**What it does:** Defines the network interface the server listens on  
**Default:** `127.0.0.1` (localhost only)  
**Options:**
- `127.0.0.1`: Local access only (development)
- `0.0.0.0`: Allow external access (production)  
**When to change:** Use `0.0.0.0` when deploying to a server accessible from other machines

```env
PORT=8011
```
**What it is:** Server port number  
**What it does:** Defines which port the FastAPI server listens on  
**Default:** `8011`  
**When to change:** If port 8011 is already in use by another application  
**Example:** `PORT=8080`

```env
RELOAD=true
```
**What it is:** Auto-reload on code changes  
**What it does:** Automatically restarts the server when code files change  
**Default:** `true`  
**Options:** `true` (development), `false` (production)  
**When to change:** Set to `false` in production for better performance

```env
LOG_LEVEL=info
```
**What it is:** Logging verbosity level  
**What it does:** Controls how much detail appears in logs  
**Default:** `info`  
**Options:** `debug`, `info`, `warning`, `error`, `critical`  
**When to change:** Use `debug` for troubleshooting, `warning` or `error` in production

---

#### Mistral AI Configuration

```env
MISTRAL_API_ENDPOINT=https://api.mistral.ai/v1/chat/completions
```
**What it is:** Mistral AI chat completions API endpoint  
**What it does:** URL for making LLM chat completion requests  
**Default:** `https://api.mistral.ai/v1/chat/completions`  
**When to change:** Only if using a custom proxy or different API version

```env
MISTRAL_MODEL=mistral-small-2503
```
**What it is:** Mistral AI model identifier  
**What it does:** Specifies which LLM model handles user queries and tool selection  
**Default:** `mistral-small-2503`  
**Options:**
- `mistral-small-2503`: Fastest, cost-effective (recommended)
- `mistral-medium`: Balanced performance
- `mistral-large`: Most capable but slower and expensive  
**When to change:** Use larger models for more complex reasoning tasks

```env
MISTRAL_API_EMBEDDING=https://api.mistral.ai/v1/embeddings
```
**What it is:** Mistral AI embeddings API endpoint  
**What it does:** URL for generating text embeddings for RAG search  
**Default:** `https://api.mistral.ai/v1/embeddings`  
**When to change:** Only if using a custom endpoint

```env
MISTRAL_EMBEDDING_MODEL=codestral-embed
```
**What it is:** Mistral AI embedding model identifier  
**What it does:** Converts text into vector embeddings for semantic search  
**Default:** `codestral-embed`  
**When to change:** If Mistral releases new embedding models

```env
MISTRAL_TEMPERATURE=0.7
```
**What it is:** LLM temperature (creativity/randomness) setting  
**What it does:** Controls randomness in LLM responses  
**Default:** `0.7`  
**Range:** `0.0` to `1.0`
- `0.0`: Deterministic, factual, consistent (same input = same output)
- `0.5`: Balanced between creativity and consistency
- `1.0`: Maximum creativity, varied, less predictable  
**Use cases:**
- `0.0-0.3`: Factual Q&A, tool selection (recommended for orchestrator)
- `0.4-0.7`: General conversation (recommended)
- `0.8-1.0`: Creative writing, brainstorming  
**When to change:** Lower for factual tasks, higher for creative tasks

```env
MISTRAL_MAX_TOKENS=500
```
**What it is:** Maximum tokens in LLM response  
**What it does:** Limits the length of AI-generated responses  
**Default:** `500`  
**What it means:** ~375 words or ~2000 characters  
**Trade-offs:**
- Higher: Longer, more detailed responses but slower and more expensive
- Lower: Shorter, concise responses but may cut off important info  
**Typical values:**
- `100-300`: Short, concise answers
- `500-1000`: Standard answers (recommended)
- `1000+`: Detailed, comprehensive responses  
**When to change:** Increase for detailed explanations, decrease for brief answers

```env
MISTRAL_MAX_CONTEXT_TOKENS=10000
```
**What it is:** Maximum tokens in conversation context  
**What it does:** Limits total conversation history sent to LLM  
**Default:** `10000`  
**What it does:** Prevents exceeding the model's context window (maximum input size)  
**When to change:** Increase for longer conversations, decrease to reduce API costs

```env
MISTRAL_API_TIMEOUT=60.0  # LLM request timeout (s)
MISTRAL_EMBEDDING_TIMEOUT=120.0  # Embedding request timeout (s)
MISTRAL_STARTUP_TIMEOUT=10.0  # Startup health-check timeout (s)
MISTRAL_STARTUP_MAX_TOKENS=10  # Tokens used for startup health check
MISTRAL_MAX_RETRIES=3  # Retry attempts for Mistral API calls
MISTRAL_EMBEDDING_BATCH_SIZE_SMALL=5  # Embedding batch size (large datasets)
MISTRAL_EMBEDDING_BATCH_SIZE_LARGE=10  # Embedding batch size (small datasets)
MISTRAL_EMBEDDING_BATCH_THRESHOLD=50  # Threshold to choose embedding batch size

RAG_MAX_CONTEXT_LENGTH=2000  # Max combined chars for RAG context
RAG_CHUNK_SIZE=500  # Document chunk size (chars)
RAG_CHUNK_OVERLAP=50  # Overlap between chunks (chars)

MAX_UPLOAD_SIZE_MB=10  # Max upload file size (MB)

DEBUG_THIRD_PARTY=false  # Enable verbose logging for 3rd-party libs
MINIMAL_LOGGING=true  # Use minimal logging output

STRICT_TOOL_MATCHING=true  # Enforce strict tool selection (anti-hallucination)

CHARS_PER_TOKEN=4  # Characters per token estimate
```

---

## Usage

### Note
The environment variables above are used to configure the application. Set required keys (e.g., `MISTRAL_API_KEY`, `MONGODB_URL`, `OPENWEATHER_API_KEY`) in your environment or a `.env` file.

3. Configure for production: set `RELOAD=false` and `HOST=0.0.0.0` if exposing externally.

4. Set up MongoDB (local or Atlas) and update `MONGODB_URL`.

5. Run the application:
   ```bash
   pip install -r requirements.txt
   python startup.py
   ```

---

## License

MIT License - Copyright (c) 2025 Mohamad Ali Ibrahim
