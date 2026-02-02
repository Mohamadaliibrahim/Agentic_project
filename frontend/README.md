﻿Perfect 👍
Here is the **cleaned and adapted version** of your **Frontend README section**, rewritten so it fits **inside the original main README**, with **all git / clone / cd references removed**.

You can paste this **directly under a “Frontend — Streamlit Chat UI” section** in your main `README.md`.

---

## Frontend — Streamlit Chat UI

Streamlit web interface for the AI chatbot backend.
Allows users to upload documents, chat with the AI, and view conversation history through a simple web UI.

---

### What This Does

* Connects to the FastAPI backend
* Provides a chat interface for LLM interaction
* Supports document upload for RAG-powered responses
* Displays conversation history per user

Built with **Streamlit** for fast setup and easy deployment.

---

### Frontend Setup

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> **Important:** Make sure the backend is already running.

Start the Streamlit app:

```powershell
python main.py
```

Open in your browser:

```
http://localhost:8501
```

---

### Configuration Reference

All frontend settings are defined in `config.py`.

#### API Settings

* `API_BASE_URL` — Backend API URL
  *(default: [http://127.0.0.1:8011](http://127.0.0.1:8011))*

#### Page Settings

* `PAGE_TITLE` — Browser tab title
  *(default: 🤖 AI Document Chat Assistant)*
* `PAGE_ICON` — Browser tab icon
  *(default: 🤖)*
* `LAYOUT` — Streamlit layout mode (`centered` or `wide`)
  *(default: wide)*

#### UI Settings

* `MAX_MESSAGE_LENGTH` — Maximum characters per message
  *(default: 1000)*
* `MAX_FILE_SIZE_MB` — Maximum upload size
  *(default: 10 MB)*
* `SUPPORTED_FILE_TYPES` — Allowed upload formats
  *(pdf, txt, csv, docx)*

#### Styling

* `PRIMARY_COLOR` — Main theme color
* `SECONDARY_COLOR` — Accent color
* `BACKGROUND_COLOR` — Page background color

#### Chat Settings

* `MAX_MESSAGES_DISPLAY` — Max messages shown in history
  *(default: 50)*
* `MESSAGE_REFRESH_INTERVAL` — Auto-refresh interval (seconds)
  *(default: 1)*

---

### How to Use

1. Create or select a user from the sidebar
2. Upload documents (optional, for RAG search)
3. Type your message and press Enter
4. View previous conversation history when needed

---

### Features

* ✅ User creation & switching
* ✅ Document upload (PDF, TXT, DOCX, CSV)
* ✅ Real-time AI responses
* ✅ Conversation history viewer
* ✅ RAG-powered document search
* ✅ Clean and responsive UI

---

### Frontend Structure

```
frontend/
├── main.py          # Streamlit app entry point
├── config.py        # UI & API configuration
├── api_client.py    # Backend API client
├── utils.py         # Helper utilities
└── requirements.txt # Python dependencies
```