﻿﻿# Frontend — Streamlit Chat UI

Streamlit web interface for the AI chatbot backend. Upload documents, chat with AI, and view conversation history.

## What This Does

Simple web UI that connects to the FastAPI backend to provide document upload, RAG-powered chat, and conversation management. Built with Streamlit for easy deployment.

## Quick Setup

Clone and install (Windows PowerShell):
```powershell
git clone <<git_path>>
cd <<The cloned file>>
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Important:** Start the backend first (see backend README), then run:
```powershell
python main.py
```

Visit http://localhost:8501 in your browser.

## Configuration Reference

All settings in `config.py` (customize via code or environment variables):

**API Settings**
- `API_BASE_URL` — Backend API URL (default: http://127.0.0.1:8011)

**Page Settings**
- `PAGE_TITLE` — Browser tab title (default: 🤖 AI Document Chat Assistant)
- `PAGE_ICON` — Browser tab icon (default: 🤖)
- `LAYOUT` — Streamlit layout mode: centered or wide (default: wide)

**UI Settings**
- `MAX_MESSAGE_LENGTH` — Maximum characters per message (default: 1000)
- `MAX_FILE_SIZE_MB` — Maximum upload size in MB (default: 10)
- `SUPPORTED_FILE_TYPES` — Allowed file types for upload (default: pdf, txt, csv, docx)

**Styling**
- `PRIMARY_COLOR` — Main theme color hex code (default: #667eea)
- `SECONDARY_COLOR` — Secondary theme color hex code (default: #764ba2)
- `BACKGROUND_COLOR` — Background color hex code (default: #fafafa)

**Chat Settings**
- `MAX_MESSAGES_DISPLAY` — Maximum messages shown in history (default: 50)
- `MESSAGE_REFRESH_INTERVAL` — Auto-refresh interval in seconds (default: 1)

## How to Use

1. **Create/Select User** — Use sidebar to create or select a user
2. **Upload Documents** (Optional) — Upload PDF/TXT/DOCX files for RAG search
3. **Chat** — Type your message and press Enter
4. **View History** — Click "Show Conversation History" to see past messages

## Features

- ✅ User management (create/switch users)
- ✅ Document upload (PDF, TXT, DOCX, CSV)
- ✅ Real-time AI chat responses
- ✅ Conversation history viewer
- ✅ RAG-powered document search
- ✅ Clean, responsive interface

## Project Structure

```
frontend/
├── main.py          # Streamlit app entry point
├── config.py        # Configuration settings
├── api_client.py    # Backend API client
├── utils.py         # Utility functions
└── requirements.txt # Python dependencies
```
