# Streamlit Frontend - Bot Chat Interface

A user-friendly Streamlit-based chat interface for interacting with the FastAPI backend bot system.

## 📋 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Introduction

This Streamlit frontend provides an intuitive chat interface for:
- Creating and managing users
- Uploading documents for RAG search
- Chatting with the intelligent bot
- Viewing conversation history
- Testing weather queries and document search

The frontend connects to the FastAPI backend API to provide a seamless user experience.

---

## ✨ Features

- **👤 User Management**: Create and select users
- **📄 Document Upload**: Upload PDF, TXT, DOCX files for RAG search
- **💬 Chat Interface**: Interactive chat with the bot
- **📜 Conversation History**: View all past messages
- **🎨 Modern UI**: Clean, intuitive Streamlit interface
- **🔄 Real-time Updates**: Live responses from the backend
- **📊 Status Indicators**: Clear feedback for all operations

---

## 📦 Prerequisites

Before you begin, ensure you have:

- **Python 3.12+** (Python 3.12 is recommended)
- **FastAPI Backend Running**: The backend must be running on `http://127.0.0.1:8011`
- **pip** (Python package installer)

### System Requirements
- Operating System: Windows, macOS, or Linux
- RAM: Minimum 2GB
- Disk Space: 100MB free space

---

## 🚀 Installation

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Activate Virtual Environment

Make sure you have activated the virtual environment created in the project root:

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

### Step 3: Install Frontend Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- **Streamlit** - Web framework for the UI
- **Requests** - HTTP library for API calls
- **python-dotenv** - Environment variable management

### Step 4: Ensure Backend is Running

Make sure the FastAPI backend is running:

```bash
# In a separate terminal, navigate to backend folder
cd ../backend
python main.py
```

The backend should be accessible at `http://127.0.0.1:8011`

### Step 5: Run the Frontend

```bash
streamlit run main.py
```

The frontend will start on `http://localhost:8501`

---

## ⚙️ Configuration

### Key Configuration Files

1. **`config.py`**: Frontend configuration (API URL, settings)
2. **`requirements.txt`**: Python dependencies

### Backend API URL

The frontend is configured to connect to the backend at `http://127.0.0.1:8011`

If your backend is running on a different URL, update `config.py`:

```python
# config.py
BACKEND_URL = "http://your-backend-url:port"
```

---

## 📖 Usage

### Starting the Frontend

1. **Ensure backend is running** at `http://127.0.0.1:8011`
2. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```
3. **Run Streamlit:**
   ```bash
   streamlit run main.py
   ```
4. **Open your browser** to `http://localhost:8501`

### Using the Interface

#### 1. Create or Select a User

On the sidebar:
- Enter a username and email
- Click "Create User"
- Or select an existing user from the dropdown

#### 2. Upload Documents (Optional)

If you want to use document search:
- Click "Upload Document" in the sidebar
- Select a PDF, TXT, or DOCX file
- Wait for upload confirmation
- Documents are now searchable

#### 3. Chat with the Bot

In the main chat area:
- Type your question in the input field
- Press Enter or click Send
- The bot will intelligently select the appropriate tool:
  - **Weather queries** → Gets real-time weather data
  - **Document questions** → Searches your uploaded documents
  - **Other questions** → Returns "I don't know" (no hallucination)

#### 4. View Conversation History

- All messages are displayed in the chat interface
- Messages are persistent for the selected user
- Scroll to see previous conversations

### Example Queries

**Weather Queries:**
- "What's the weather in Paris?"
- "How hot is it in Dubai?"
- "Temperature in New York?"

**Document Search:**
- "Find information about shipping rates"
- "Search my documents for contract details"
- "What does my document say about pricing?"

**Out of Scope (Returns "I don't know"):**
- "What is 2+2?"
- "Tell me a joke"
- "Who is the president?"

---

## 🗂️ Project Structure

```
frontend/
├── main.py              # Main Streamlit application
├── api_client.py        # Backend API client functions
├── config.py            # Frontend configuration
├── utils.py             # Utility functions
├── requirements.txt     # Frontend dependencies
└── README.md           # This file
```

### File Descriptions

- **`main.py`**: Main Streamlit application with UI components
- **`api_client.py`**: Functions to interact with backend API (create user, upload document, send message)
- **`config.py`**: Configuration settings (backend URL, defaults)
- **`utils.py`**: Helper functions for the frontend
- **`requirements.txt`**: List of required Python packages

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Cannot Connect to Backend
```
Error: Connection refused or backend not accessible
```
**Solutions:**
- Ensure backend is running: `cd ../backend && python main.py`
- Check backend URL in `config.py`
- Verify backend is accessible at `http://127.0.0.1:8011/health`

#### 2. Port 8501 Already in Use
```
Error: Port 8501 is already in use
```
**Solution:** Stop other Streamlit instances or use a different port:
```bash
streamlit run main.py --server.port 8502
```

#### 3. Module Not Found Errors
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

#### 4. Virtual Environment Not Activated
**Solution:** Activate the virtual environment:
```bash
# Windows
..\myvenv\Scripts\Activate.ps1

# Mac/Linux
source ../myvenv/bin/activate
```

#### 5. Document Upload Fails
**Solutions:**
- Check file size (default max: 10MB)
- Ensure file format is supported (PDF, TXT, DOCX)
- Verify backend is running and accessible

#### 6. User Creation Fails
**Solutions:**
- Ensure backend MongoDB is running
- Check backend logs in `../backend/logs/`
- Verify backend health at `http://127.0.0.1:8011/health`

### Debugging

#### Check Backend Health
```bash
curl http://127.0.0.1:8011/health
```

#### Test Backend API Directly
```bash
# Test user creation
curl -X POST "http://127.0.0.1:8011/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com"}'
```

#### Check Streamlit Logs
Streamlit displays logs in the terminal where it's running. Check for error messages there.

---

## 🎨 Customization

### Changing Backend URL

Edit `config.py`:
```python
BACKEND_URL = "http://your-custom-backend:port"
```

### Changing Page Title

Edit `main.py`:
```python
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🤖"
)
```

### Customizing UI Theme

Create `.streamlit/config.toml` in the frontend directory:
```toml
[theme]
primaryColor="#F63366"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#262730"
font="sans serif"
```

---

## 🔗 Related Documentation

- **Backend README**: See `../backend/README.md` for backend setup
- **Streamlit Documentation**: https://docs.streamlit.io/
- **Backend API Documentation**: http://127.0.0.1:8011/docs
