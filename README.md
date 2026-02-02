# Agentic Project — AI RAG Chatbot (FastAPI + Streamlit)

End-to-end **AI Document Chatbot** using **FastAPI (backend)** and **Streamlit (frontend)**.
Supports **RAG (Retrieval-Augmented Generation)**, document upload, structured LLM responses,
weather queries, and persistent conversation history.

---

## Overview

This project provides a full-stack AI chatbot system:

- **Backend (FastAPI)**  
  Handles LLM orchestration, document embedding & retrieval (RAG), weather queries, and data persistence.
- **Frontend (Streamlit)**  
  User-friendly web UI to chat with the AI, upload documents, and manage conversations.

---

## Architecture

User → Streamlit Frontend → FastAPI Backend  
FastAPI integrates:
- Mistral AI (Chat + Embeddings)
- FAISS Vector Search
- MongoDB (Users, Messages, Documents)
- OpenWeather API (optional)

---

## Tech Stack

**Backend**
- FastAPI
- Mistral AI
- FAISS
- MongoDB
- OpenWeather API

**Frontend**
- Streamlit
- REST API integration

---

## Repository Structure

```
Agentic_project/
├── backend/
│   ├── startup.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── orchestrator.py
│   │   ├── mistral_service.py
│   │   ├── rag_service.py
│   │   └── bot_tools/
│   ├── database/
│   ├── routes/
│   ├── logs/
│   └── vector_storage/
│
├── frontend/
│   ├── main.py
│   ├── config.py
│   ├── api_client.py
│   ├── utils.py
│   └── requirements.txt
│
└── README.md
```

---

## Backend — FastAPI RAG Chatbot

### What It Does

- AI chatbot with RAG over uploaded documents
- Weather information (optional)
- Persistent conversation history
- User and document management
- Tool-based orchestration to reduce hallucinations

---

### Backend Setup

```powershell
git clone git@github.com:Mohamadaliibrahim/Agentic_project.git
cd Agentic_project/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Environment Variables (`backend/.env`)

```env
MISTRAL_API_KEY=your_key_here
MONGODB_URL=mongodb://localhost:27017
```

#### Run Backend

```powershell
python main.py
```

API Docs:
http://127.0.0.1:8011/docs

---

## Frontend — Streamlit Chat UI

### Frontend Setup

```powershell
cd Agentic_project/frontend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Make sure backend is running first

```powershell
python main.py
```

Open:
http://localhost:8501

---

## How to Use

1. Start backend
2. Start frontend
3. Create or select a user
4. Upload documents (optional)
5. Chat with the AI
6. View conversation history

---

## Features

- Retrieval-Augmented Generation (RAG)
- Document upload & management
- Persistent conversations
- Modular & extensible architecture
- Clean UI and API separation
