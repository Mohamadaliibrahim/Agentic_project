# FastAPI Mini Project - Intelligent Bot System

A production-ready full-stack application with FastAPI backend and Streamlit frontend, featuring intelligent orchestration, RAG (Retrieval-Augmented Generation) document search, weather queries, and LLM-powered tool selection using Mistral AI.

## 📋 Overview

This project consists of two main components:

1. **Backend** (`/backend`) - FastAPI REST API with intelligent bot orchestration
2. **Frontend** (`/frontend`) - Streamlit chat interface for user interaction

---

## 🎯 Quick Start

### Prerequisites

- Python 3.12+
- MongoDB (local or Atlas)
- Git
- Mistral AI API Key ([Get it here](https://console.mistral.ai/))
- OpenWeatherMap API Key ([Get it here](https://openweathermap.org/api))

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/Mohamadaliibrahim/fastapi_mini_project.git
cd fastapi_mini_project
```

#### 2. Create and Activate Virtual Environment

**On Windows:**
```powershell
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv myvenv
source myvenv/bin/activate
```

#### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 4. Configure Backend

Create a `.env` file in the `backend` directory:

```env
# Required Configuration
MISTRAL_API_KEY=your_mistral_api_key_here
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=bot_database
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

#### 5. Start MongoDB

```bash
# Windows
net start MongoDB

# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

#### 6. Run the Backend

```bash
python main.py
```

Backend will start on `http://127.0.0.1:8011`

#### 7. Install Frontend Dependencies (in a new terminal)

```bash
cd frontend
pip install -r requirements.txt
```

#### 8. Run the Frontend

```bash
streamlit run main.py
```

Frontend will start on `http://localhost:8501`

---

## 📚 Documentation

### 📖 Detailed Documentation

For comprehensive setup, configuration, and usage instructions:

- **[Backend Documentation](./backend/README.md)** - Complete backend setup, API documentation, configuration, troubleshooting
- **[Frontend Documentation](./frontend/README.md)** - Frontend installation, usage guide, customization

---

## ✨ Features

### Backend Features
- 🤖 **Intelligent Tool Selection** - LLM-powered orchestrator
- 📄 **RAG Document Search** - Semantic search through uploaded documents
- 🌤️ **Weather Queries** - Real-time weather information
- 🚫 **Anti-Hallucination** - Strict tool matching prevents out-of-scope responses
- 📝 **Centralized Prompt Management** - Edit prompts without code changes
- 🔧 **Zero Hardcoded Values** - All configuration in environment variables
- 📊 **Comprehensive Logging** - Detailed debug, error, and prompt logs
- 🗄️ **MongoDB Integration** - Persistent storage
- ⚡ **Async Processing** - High-performance architecture

### Frontend Features
- 👤 **User Management** - Create and manage users
- 📄 **Document Upload** - Upload documents for RAG search
- 💬 **Chat Interface** - Interactive bot conversation
- 📜 **Conversation History** - View past messages
- 🎨 **Modern UI** - Clean Streamlit interface

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              Streamlit Frontend (:8501)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend (:8011)                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Orchestrator (LLM Tool Selector)          │  │
│  └───────┬──────────────────────────────────────┬───────┘  │
│          │                                       │          │
│  ┌───────▼────────┐                   ┌─────────▼───────┐  │
│  │ Weather Tool   │                   │   RAG Tool      │  │
│  │ (OpenWeather)  │                   │ (Vector Search) │  │
│  └────────────────┘                   └─────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Mistral AI Service                      │  │
│  │        (LLM Calls + Embeddings)                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │
         ┌───────────────┴──────────────┐
         │                              │
    ┌────▼─────┐                  ┌────▼──────┐
    │ MongoDB  │                  │ ChromaDB  │
    │ (Data)   │                  │ (Vectors) │
    └──────────┘                  └───────────┘
```

---

## 🗂️ Project Structure

```
fastapi_mini_project/
├── README.md                      # This file - Project overview
│
├── backend/                       # FastAPI Backend
│   ├── README.md                 # Backend documentation
│   ├── main.py                   # Application entry point
│   ├── requirements.txt          # Backend dependencies
│   ├── prompts.txt              # LLM prompts configuration
│   ├── .env                      # Environment variables (create this)
│   ├── core/                     # Core business logic
│   ├── database/                 # Database adapters
│   ├── routes/                   # API endpoints
│   ├── logs/                     # Application logs
│   └── vector_storage/           # Vector database storage
│
├── frontend/                      # Streamlit Frontend
│   ├── README.md                 # Frontend documentation
│   ├── main.py                   # Frontend entry point
│   ├── requirements.txt          # Frontend dependencies
│   ├── api_client.py             # Backend API client
│   ├── config.py                 # Frontend configuration
│   └── utils.py                  # Utility functions
│
└── myvenv/                        # Virtual environment (created during setup)
```

---

## 🔗 Access Points

Once both backend and frontend are running:

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://127.0.0.1:8011
- **API Documentation (Swagger)**: http://127.0.0.1:8011/docs
- **API Documentation (ReDoc)**: http://127.0.0.1:8011/redoc
- **Health Check**: http://127.0.0.1:8011/health

---

## 🎯 Usage Examples

### Via Frontend (Recommended)

1. Open http://localhost:8501
2. Create a user
3. Upload documents (optional)
4. Start chatting!

### Via API (Direct)

```bash
# Ask about weather
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "user_input": "What is the weather in Paris?"}'

# Search documents
curl -X POST "http://127.0.0.1:8011/orchestrator/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "user_input": "Find information about shipping"}'
```

---

## 🔍 Troubleshooting

### Backend Not Starting?
- Check MongoDB is running
- Verify API keys in `.env`
- See [Backend README](./backend/README.md#troubleshooting)

### Frontend Not Connecting?
- Ensure backend is running on port 8011
- Check backend health: `curl http://127.0.0.1:8011/health`
- See [Frontend README](./frontend/README.md#troubleshooting)

### Both Components Not Working?
1. Check virtual environment is activated
2. Verify all dependencies installed
3. Check logs in `backend/logs/`

---

## 📖 Next Steps

1. **Read Backend Documentation**: [backend/README.md](./backend/README.md)
2. **Read Frontend Documentation**: [frontend/README.md](./frontend/README.md)
3. **Explore API**: http://127.0.0.1:8011/docs
4. **Start Chatting**: http://localhost:8501

---

## 🛠️ Technology Stack

**Backend:**
- FastAPI - Web framework
- Mistral AI - LLM and embeddings
- MongoDB - Database
- ChromaDB - Vector storage
- LangChain - Document processing

**Frontend:**
- Streamlit - UI framework
- Requests - HTTP client

**DevOps:**
- Python-dotenv - Configuration
- Uvicorn - ASGI server


