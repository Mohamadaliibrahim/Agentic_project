import streamlit as st
import requests
import json
from datetime import datetime
import time
import uuid
from typing import Dict, Any, List, Optional
import os
import subprocess
import sys

# Import our custom modules
try:
    from api_client import api_client
    from utils import SessionManager, format_timestamp, format_file_size, create_chat_bubble
    from config import config
except ImportError:
    # Fallback if modules aren't available
    class api_client:
        @staticmethod
        def create_user(): return None
        @staticmethod
        def get_chat_collection(user_id): return []
         # Message input
        st.markdown("---")
        
        # Create a form for message input@staticmethod
        def send_message(user_id, message, chat_id=None): return None
        @staticmethod
        def upload_document(user_id, file): return None
        @staticmethod
        def get_user_documents(user_id): return []
        @staticmethod
        def check_health(): return False
        @staticmethod
        def update_message(message_id, new_content): return None
        @staticmethod
        def update_message_and_regenerate(message_id, new_content): return None
    
    SessionManager = type('SessionManager', (), {
        'init_session': lambda: None,
        'get': lambda key, default=None: st.session_state.get(key, default),
        'set': lambda key, value: setattr(st.session_state, key, value)
    })()
    
    format_timestamp = lambda x: x
    format_file_size = lambda x: f"{x} bytes"
    create_chat_bubble = lambda msg, is_user: f"<div>{msg.get('content', '')}</div>"
    
    config = type('config', (), {
        'API_BASE_URL': 'http://127.0.0.1:8011',
        'PAGE_TITLE': '🤖 AI Document Chat Assistant',
        'PAGE_ICON': '🤖'
    })()


class ChatBot:
    def __init__(self):
        self.api_client = api_client
        
    def create_user(self) -> Optional[str]:
        """Create a new user and return user ID"""
        return self.api_client.create_user()
    
    def get_chat_collection(self, user_id: str) -> List[Dict]:
        """Get all chats for a user"""
        return self.api_client.get_chat_collection(user_id)
    
    def get_chat_messages(self, chat_id: str) -> List[Dict]:
        """Get all messages for a specific chat"""
        return self.api_client.get_chat_messages(chat_id)
    
    def send_message(self, user_id: str, message: str, context: Optional[Dict] = None) -> Optional[Dict]:
        """Send a message using the intelligent orchestrator (handles weather, documents, general questions, etc.)"""
        return self.api_client.send_orchestrated_message(user_id, message, context)
    
    def upload_document(self, user_id: str, file) -> Optional[Dict]:
        """Upload a document"""
        return self.api_client.upload_document(user_id, file)
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get all documents for a user"""
        return self.api_client.get_user_documents(user_id)
    
    def check_health(self) -> bool:
        """Check API health"""
        return self.api_client.check_health()
    
    def update_chat_title(self, chat_id: str, new_title: str) -> Optional[Dict]:
        """Update chat title"""
        return self.api_client.update_chat_title(chat_id, new_title)
    
    def update_message(self, message_id: str, new_user_message: str) -> Optional[Dict]:
        """Update a message content"""
        return self.api_client.update_message(message_id, new_user_message)
    
    def update_message_and_regenerate(self, message_id: str, new_user_message: str) -> Optional[Dict]:
        """Update a message content and regenerate AI response"""
        return self.api_client.update_message_and_regenerate(message_id, new_user_message)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        return self.api_client.delete_document(document_id)


def run_streamlit_app():
    """Main Streamlit application function"""
    # Configure Streamlit page
    st.set_page_config(
        page_title=config.PAGE_TITLE,
        page_icon=config.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for styling
    st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
        color: #333333;
    }
    
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
        color: #333333;
    }
    
    .source-chip {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        background-color: #4a69bd;
        color: #ffffff;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 500;
        border: 1px solid #3c5aa6;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    .stats-container {
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    
    .edit-form {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 1rem;
        background-color: #f8f9fb;
        margin: 1rem 0;
    }
    
    .edit-button {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        background-color: #667eea;
        color: white;
        border: none;
        cursor: pointer;
    }
    
    .edit-button:hover {
        background-color: #5a6fd8;
    }
</style>
""", unsafe_allow_html=True)

    # Configuration
    API_BASE_URL = config.API_BASE_URL

    # Initialize session state
    SessionManager.init_session()

    # Initialize the chatbot
    chatbot = ChatBot()

    # Main header
    st.markdown('<div class="main-header">🤖 AI Document Chat Assistant</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🎛️ Control Panel</div>', unsafe_allow_html=True)
        
        # User management
        user_id = SessionManager.get("user_id")
        if user_id is None:
            if st.button("🚀 Start New Session", type="primary"):
                new_user_id = chatbot.create_user()
                if new_user_id:
                    SessionManager.set("user_id", new_user_id)
                    st.success(f"Session started! User ID: {new_user_id[:8]}...")
                    st.rerun()
        else:
            # st.success(f"👤 Active User: {user_id[:8]}...")
            st.success(f"Hello User!")
            
            # if st.button("🔄 New Session"):
            #     # Reset session
            #     SessionManager.set("user_id", None)
            #     SessionManager.set("current_chat_id", None)
            #     SessionManager.set("messages", [])
            #     SessionManager.set("chats", [])
            #     st.rerun()
        
        if user_id:
            st.markdown("---")
            
            if st.button("➕ New Chat", type="primary", use_container_width=True):
                SessionManager.set("current_chat_id", None)
                SessionManager.set("messages", [])
                st.success("🆕 Started new chat! Send a message to begin.")
                st.rerun()
            st.markdown("---")
            # Chat management
            st.markdown("### 💬 Chat History")
            
            # Refresh chats
            # if st.button("🔄 Refresh Chats"):
            #     chats = chatbot.get_chat_collection(user_id)
            #     SessionManager.set("chats", chats)
            
            # Load chats
            chats = SessionManager.get("chats", [])
            if not chats:
                chats = chatbot.get_chat_collection(user_id)
                SessionManager.set("chats", chats)
            st.markdown("---")
            # Auto-load messages for current chat if not already loaded
            current_chat_id = SessionManager.get("current_chat_id")
            messages = SessionManager.get("messages", [])
            if current_chat_id and not messages:
                # Load messages for the current chat
                chat_messages = chatbot.get_chat_messages(current_chat_id)
                if chat_messages:
                    SessionManager.set("messages", chat_messages)
            
            if chats:
                # Sort chats by creation date (newest first)
                sorted_chats = sorted(chats, key=lambda x: x.get('creation', ''), reverse=True)
                
                # Create a scrollable container for chats
                st.markdown("#### 📋 Your Chats")
                current_chat_id = SessionManager.get("current_chat_id")
                
                for i, chat in enumerate(sorted_chats):
                    chat_preview = chat["chatTitle"][:25] + "..." if len(chat["chatTitle"]) > 25 else chat["chatTitle"]
                    
                    # Create columns for chat button and edit button
                    col_chat, col_edit = st.columns([3, 1])
                    
                    with col_chat:
                        # Highlight current chat
                        button_type = "primary" if chat["chatId"] == current_chat_id else "secondary"
                        chat_emoji = "🔥" if chat["chatId"] == current_chat_id else "💬"
                        
                        if st.button(f"{chat_emoji} {chat_preview}", key=f"chat_{chat['chatId']}", type=button_type):
                            SessionManager.set("current_chat_id", chat["chatId"])
                            # Load messages for this chat
                            chat_messages = chatbot.get_chat_messages(chat["chatId"])
                            SessionManager.set("messages", chat_messages or [])
                            st.success(f"Switched to: {chat_preview}")
                            st.rerun()
                    
                    with col_edit:
                        # Edit title button
                        if st.button("✏️", key=f"edit_{chat['chatId']}", help="Edit chat title"):
                            SessionManager.set("editing_chat_id", chat["chatId"])
                            SessionManager.set("editing_chat_title", chat["chatTitle"])
                            st.rerun()
                    
                    # Show edit dialog if this chat is being edited
                    if SessionManager.get("editing_chat_id") == chat["chatId"]:
                        with st.form(f"edit_form_{chat['chatId']}"):
                            new_title = st.text_input(
                                "New chat title:",
                                value=SessionManager.get("editing_chat_title", chat["chatTitle"]),
                                key=f"title_input_{chat['chatId']}"
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Save", type="primary"):
                                    if new_title.strip():
                                        result = chatbot.update_chat_title(chat["chatId"], new_title.strip())
                                        if result:
                                            st.success("✅ Title updated!")
                                            # Refresh chats to show updated title
                                            chats = chatbot.get_chat_collection(user_id)
                                            SessionManager.set("chats", chats)
                                            SessionManager.set("editing_chat_id", None)
                                            SessionManager.set("editing_chat_title", None)
                                            st.rerun()
                                        else:
                                            st.error("Failed to update title")
                                    else:
                                        st.error("Title cannot be empty")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel"):
                                    SessionManager.set("editing_chat_id", None)
                                    SessionManager.set("editing_chat_title", None)
                                    st.rerun()
            else:
                st.info("No previous chats found. Start a new conversation!")
            
            # New chat button
            # st.markdown("---")
            # if st.button("➕ New Chat", type="primary", use_container_width=True):
            #     SessionManager.set("current_chat_id", None)
            #     SessionManager.set("messages", [])
            #     st.success("🆕 Started new chat! Send a message to begin.")
            #     st.rerun()
            
            st.markdown("---")
            
            # Document management
            st.markdown("### 📄 Document Management")
            
            # Document upload
            uploaded_file = st.file_uploader(
                "Upload Document", 
                type=['pdf', 'txt', 'csv', 'docx'],
                help="Upload PDF, TXT, CSV, or DOCX files"
            )
            
            if uploaded_file and st.button("📤 Upload Document"):
                # Check file size and show appropriate message
                file_size = len(uploaded_file.getvalue()) if hasattr(uploaded_file, 'getvalue') else 0
                file_size_mb = file_size / (1024 * 1024)
                
                if file_size_mb > 1:  # Large files (>1MB)
                    spinner_text = f"⏳ Processing large document ({file_size_mb:.1f}MB)... This may take a few minutes."
                else:
                    spinner_text = "📤 Uploading document..."
                
                with st.spinner(spinner_text):
                    result = chatbot.upload_document(user_id, uploaded_file)
                    if result:
                        st.success(f"✅ Document uploaded: {result['filename']}")
                        st.info(f"📊 Created {result['total_chunks']} chunks")
                    else:
                        st.error("❌ Failed to upload document")
            
            # Show user documents
            documents = chatbot.get_user_documents(user_id)
            if documents:
                st.markdown("#### 📚 Your Documents")
                for doc in documents:
                    with st.expander(f"📄 {doc['filename']}"):
                        col_info, col_delete = st.columns([3, 1])
                        
                        with col_info:
                            st.write(f"**Type:** {doc['file_type']}")
                            st.write(f"**Chunks:** {doc['total_chunks']}")
                            st.write(f"**Size:** {format_file_size(doc['file_size'])}")
                            st.write(f"**Uploaded:** {doc['upload_date']}")
                        
                        with col_delete:
                            # Check if this document is being confirmed for deletion
                            confirm_key = f"confirm_delete_{doc['document_id']}"
                            is_confirming = SessionManager.get(confirm_key, False)
                            
                            if not is_confirming:
                                if st.button("🗑️ Delete", key=f"delete_doc_{doc['document_id']}", help="Delete this document"):
                                    SessionManager.set(confirm_key, True)
                                    st.rerun()
                            else:
                                st.warning("⚠️ Are you sure?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ Yes", key=f"yes_{doc['document_id']}", type="primary"):
                                        with st.spinner("Deleting..."):
                                            success = chatbot.delete_document(doc['document_id'])
                                            if success:
                                                st.success("✅ Deleted!")
                                                SessionManager.set(confirm_key, False)
                                                st.rerun()
                                            else:
                                                st.error("❌ Failed")
                                                SessionManager.set(confirm_key, False)
                                with col_no:
                                    if st.button("❌ No", key=f"no_{doc['document_id']}"):
                                        SessionManager.set(confirm_key, False)
                                        st.rerun()

    # Main content area
    user_id = SessionManager.get("user_id")
    if user_id is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 3rem;">
                <h2>🌟 Welcome to AI Document Chat Assistant!</h2>
                <p style="font-size: 1.2rem; color: #666;">
                    Your intelligent companion for document analysis and conversation
                </p>
                <br>
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 2rem; border-radius: 15px;">
                    <h3>🚀 Getting Started</h3>
                    <p>1. Click "Start New Session" in the sidebar</p>
                    <p>2. Upload your documents</p>
                    <p>3. Start chatting with your AI assistant!</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        # #Chat interface
        # col1, co l2 = st.columns([3, 1])
        
        # with col1:
        st.markdown("### 💬 Chat Interface")
        
        # Quick Questions Section
        with st.expander("🎯 **Quick Questions** - Click to ask instantly!", expanded=False):
            st.markdown("**💫 Popular questions - Click any button to instantly submit the question:**")
            st.markdown("*These are common questions that users frequently ask. Perfect for getting started!*")
            
            # Create columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🛠️ What are the tools used in CMA CGM?", key="quick_q1", use_container_width=True):
                    # Set the question in session state to populate input box
                    SessionManager.set("selected_question", "what are the tools used in cma cgm?")
                    st.rerun()
                
                if st.button("📋 How to open a ticket for Dataiku?", key="quick_q2", use_container_width=True):
                    SessionManager.set("selected_question", "how to open a ticket for dataiku?")
                    st.rerun()
            
            with col2:
                if st.button("🌤️ What is the weather in Japan?", key="quick_q3", use_container_width=True):
                    SessionManager.set("selected_question", "what is the weather in japan?")
                    st.rerun()
                
                if st.button("🎫 How to open an EUP ticket?", key="quick_q4", use_container_width=True):
                    SessionManager.set("selected_question", "how to open an EUP ticket?")
                    st.rerun()
            
            # Add some styling
            st.markdown("""
            <style>
            .stButton > button {
                height: 3rem;
                font-size: 0.9rem;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                transition: all 0.2s ease;
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Show current chat info with editable title (only when editing)
        current_chat_id = SessionManager.get("current_chat_id")
        if current_chat_id:
            # Find current chat details
            chats = SessionManager.get("chats", [])
            current_chat = next((chat for chat in chats if chat["chatId"] == current_chat_id), None)
            
            if current_chat:
                # Check if we're editing the current chat title
                editing_current = SessionManager.get("editing_current_chat_title", False)
                
                if editing_current:
                    # Show inline title editor
                    with st.form("edit_current_title_form"):
                        col_title, col_actions = st.columns([3, 1])
                        
                        with col_title:
                            new_title = st.text_input(
                                "Chat Title:", 
                                value=current_chat.get("chatTitle", "Untitled Chat"),
                                key="current_title_input"
                            )
                        
                        with col_actions:
                            col_save, col_cancel = st.columns(2)
                            
                            with col_save:
                                if st.form_submit_button("💾", help="Save title"):
                                    if new_title.strip():
                                        result = chatbot.update_chat_title(current_chat_id, new_title.strip())
                                        if result:
                                            st.success("✅ Title updated!")
                                            # Refresh chats
                                            chats = chatbot.get_chat_collection(user_id)
                                            SessionManager.set("chats", chats)
                                            SessionManager.set("editing_current_chat_title", False)
                                            st.rerun()
                                        else:
                                            st.error("Failed to update title")
                                    else:
                                        st.error("Title cannot be empty")
                            
                            with col_cancel:
                                if st.form_submit_button("❌", help="Cancel"):
                                    SessionManager.set("editing_current_chat_title", False)
                                    st.rerun()
            
            # Auto-refresh messages if current chat exists but no messages are loaded
            messages = SessionManager.get("messages", [])
            if not messages:
                with st.spinner("Loading chat messages..."):
                    chat_messages = chatbot.get_chat_messages(current_chat_id)
                    if chat_messages:
                        SessionManager.set("messages", chat_messages)
                        st.rerun()
        
        # Display messages in a scrollable container
        messages = SessionManager.get("messages", [])
        
        if messages:
            # Create a container with fixed height and scrolling
            with st.container():
                st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True)
                
                for i, message in enumerate(messages):
                    # Handle different message formats from API
                    user_type = message.get("userType") or message.get("user_type") or message.get("type", "unknown")
                    content = message.get("content") or message.get("message") or message.get("user_message") or message.get("text", "")
                    timestamp = message.get("timestamp") or message.get("created_at") or message.get("date", "")
                    sources = message.get("sources", [])
                    message_id = message.get("message_id")  # Get message_id for editing
                    
                    if user_type == "user":
                        # Check if this message is being edited
                        edit_key = f"editing_message_{message_id}" if message_id else f"editing_message_{i}"
                        is_editing = SessionManager.get(edit_key, False)
                        
                        if not is_editing:
                            # Display user message with compact action buttons
                            st.markdown(f"""
                            <div class="user-message-container" style="background: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; position: relative;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                    <div style="flex: 1; margin-right: 15px;">
                                        <strong>👤 You:</strong> <small style="color: #666; margin-left: 10px;">{format_timestamp(timestamp)}</small><br>
                                        <div style="margin-top: 8px; font-size: 14px; line-height: 1.4;">
                                            {content}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Edit button - clean and user-friendly
                            if message_id:  # Only show edit button if we have a message_id
                                col_edit, col_spacer = st.columns([2, 10])
                                with col_edit:
                                    if st.button("✏️ Edit Message", key=f"edit_btn_{message_id}", help="Edit and regenerate response", use_container_width=True, type="secondary"):
                                        SessionManager.set(edit_key, True)
                                        SessionManager.set(f"edit_content_{message_id}", content)
                                        st.rerun()
                            
                            # Add some spacing after button
                            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                        else:
                            # Show edit form
                            st.markdown("### ✏️ Edit Message")
                            
                            with st.form(f"edit_message_form_{message_id}"):
                                current_content = SessionManager.get(f"edit_content_{message_id}", content)
                                new_content = st.text_area(
                                    "Edit your message:",
                                    value=current_content,
                                    height=100,
                                    key=f"edit_text_{message_id}"
                                )
                                
                                col_save, col_cancel = st.columns(2)
                                
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        if new_content.strip() and new_content != content:
                                            with st.spinner("Updating message and generating new response..."):
                                                # Update the message and regenerate AI response in one call
                                                result = chatbot.update_message_and_regenerate(message_id, new_content.strip())
                                                if result:
                                                    # Find the message index to update it in place
                                                    message_index = next((idx for idx, msg in enumerate(messages) 
                                                                        if msg.get("message_id") == message_id), None)
                                                    
                                                    if message_index is not None:
                                                        # Update the message in place with new content and AI response
                                                        updated_messages = messages.copy()
                                                        updated_messages[message_index]["content"] = result["user_message"]
                                                        updated_messages[message_index]["user_message"] = result["user_message"]
                                                        updated_messages[message_index]["assistant_message"] = result["assistant_message"]
                                                        
                                                        # Remove all messages after this one (subsequent conversation)
                                                        updated_messages = updated_messages[:message_index + 1]
                                                        
                                                        # Add the assistant response as a separate message if not already there
                                                        # Check if the next message is the assistant response for this message
                                                        if message_index + 1 < len(messages):
                                                            next_msg = messages[message_index + 1]
                                                            if (next_msg.get("userType") in ["bot", "assistant"] and 
                                                                next_msg.get("message_id") == message_id):
                                                                # Update the assistant message
                                                                updated_messages.append({
                                                                    "content": result["assistant_message"],
                                                                    "assistant_message": result["assistant_message"],
                                                                    "userType": "bot",
                                                                    "timestamp": result["date"],
                                                                    "message_id": message_id,
                                                                    "sources": []
                                                                })
                                                        else:
                                                            # Add the assistant response
                                                            updated_messages.append({
                                                                "content": result["assistant_message"],
                                                                "assistant_message": result["assistant_message"],
                                                                "userType": "bot",
                                                                "timestamp": result["date"],
                                                                "message_id": message_id,
                                                                "sources": []
                                                            })
                                                        
                                                        SessionManager.set("messages", updated_messages)
                                                        st.success("✅ Message updated and new response generated!")
                                                    
                                                    # Clear editing state
                                                    SessionManager.set(edit_key, False)
                                                    SessionManager.set(f"edit_content_{message_id}", None)
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Failed to update message")
                                        elif new_content == content:
                                            st.info("No changes made")
                                            SessionManager.set(edit_key, False)
                                            st.rerun()
                                        else:
                                            st.error("Message cannot be empty")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel"):
                                        SessionManager.set(edit_key, False)
                                        SessionManager.set(f"edit_content_{message_id}", None)
                                        st.rerun()
                        
                    elif user_type in ["bot", "assistant"]:
                        # Assistant message (no editing allowed)
                        assistant_content = message.get("assistant_message") or message.get("content") or message.get("message") or ""
                        st.markdown(f"""
                        <div class="chat-message assistant-message">
                            <strong>🤖 Assistant:</strong> <small style="color: #999; float: right;">Received: {format_timestamp(timestamp)}</small><br>
                            {assistant_content}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display sources if available (but hidden as requested)
                        if sources:
                            # Sources are hidden per user request
                            pass
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Auto-scroll to bottom
                st.markdown("""
                <script>
                setTimeout(function() {
                    var chatContainer = document.getElementById('chat-container');
                    if (chatContainer) {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                }, 100);
                </script>
                """, unsafe_allow_html=True)
        else:
            # Show helpful message when no messages exist
            current_chat_id = SessionManager.get("current_chat_id")
            if current_chat_id:
                st.info("💬 This chat is empty. Send your first message below!")
            else:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; background-color: #f0f2f6; border-radius: 10px; margin: 1rem 0;">
                    <h3>🚀 Welcome to AI Chat Assistant!</h3>
                    <p style="margin-bottom: 1rem;">Start a conversation by typing your message below.</p>
                    <p style="color: #666; font-size: 0.9em;">
                        💡 <strong>Tip:</strong> Your first message will become the chat title, which you can edit anytime by clicking the ✏️ icon.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        

        # Add some padding at the bottom to ensure messages aren't hidden behind fixed input
        st.markdown("<div style='padding-bottom: 150px;'></div>", unsafe_allow_html=True)

    # Fixed message input at bottom of page
    st.markdown("""
    <style>
    .fixed-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 2px solid #e6e6e6;
        padding: 15px 20px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 999;
    }
    
    /* Adjust for Streamlit's sidebar */
    @media (min-width: 768px) {
        .fixed-input-container {
            left: 21rem; /* Account for sidebar width */
        }
    }
    
    /* Make sure the input area has proper styling */
    .fixed-input-container .stForm {
        margin-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create fixed input container
    with st.container():
        st.markdown('<div class="fixed-input-container">', unsafe_allow_html=True)
        
        # Handle selected questions (Quick Questions or message resend)
        selected_question = SessionManager.get("selected_question")
        
        # Enhanced JavaScript for Enter/Shift+Enter handling that works with Streamlit
        st.markdown("""
        <script>
        // Use a more aggressive approach to ensure the event handler works
        function setupMessageInputHandler() {
            // Wait a bit for Streamlit to render the components
            setTimeout(function() {
                // Find all textareas (be more flexible with selectors)
                const textareas = document.querySelectorAll('textarea');
                
                textareas.forEach(function(textarea) {
                    // Check if this textarea is likely our message input
                    const placeholder = textarea.placeholder || '';
                    if (placeholder.includes('Ask me anything') || 
                        textarea.getAttribute('aria-label') === 'Type your message...' ||
                        textarea.closest('[data-testid="stForm"]')) {
                        
                        // Remove existing listeners to avoid duplicates
                        textarea.removeEventListener('keydown', handleMessageKeyDown);
                        
                        // Add our custom handler
                        textarea.addEventListener('keydown', handleMessageKeyDown);
                        
                        // Also add focus styling
                        textarea.style.border = '2px solid #ccc';
                        textarea.addEventListener('focus', function() {
                            this.style.border = '2px solid #0066cc';
                        });
                        textarea.addEventListener('blur', function() {
                            this.style.border = '2px solid #ccc';
                        });
                    }
                });
            }, 100);
        }
        
        function handleMessageKeyDown(event) {
            if (event.key === 'Enter') {
                if (event.shiftKey) {
                    // Shift+Enter: Allow new line (do nothing, let default behavior happen)
                    return true;
                } else {
                    // Enter alone: Submit the form
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Find the submit button in the same form
                    const form = event.target.closest('form') || 
                                event.target.closest('[data-testid="stForm"]') ||
                                document.querySelector('[data-testid="stForm"]');
                    
                    if (form) {
                        const submitBtn = form.querySelector('button[kind="primaryFormSubmit"]') ||
                                        form.querySelector('button[type="submit"]') ||
                                        form.querySelector('button:contains("Send")') ||
                                        form.querySelector('.stButton button');
                        
                        if (submitBtn) {
                            submitBtn.click();
                        }
                    }
                    
                    return false;
                }
            }
        }
        
        // Run setup immediately
        setupMessageInputHandler();
        
        // Run setup when DOM changes (Streamlit updates)
        if (typeof window.messageInputObserver !== 'undefined') {
            window.messageInputObserver.disconnect();
        }
        
        window.messageInputObserver = new MutationObserver(function(mutations) {
            let shouldSetup = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    shouldSetup = true;
                }
            });
            if (shouldSetup) {
                setupMessageInputHandler();
            }
        });
        
        window.messageInputObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also setup on window load and Streamlit events
        window.addEventListener('load', setupMessageInputHandler);
        
        // Streamlit-specific: Run after Streamlit finishes rendering
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(setupMessageInputHandler, 200);
        });
        </script>
        """, unsafe_allow_html=True)

        # Create a form for message input with enhanced Enter key handling
        with st.form("message_form", clear_on_submit=True):
            # Add inline CSS and JavaScript for better Enter key handling
            st.markdown("""
            <style>
            /* Style the message input area */
            .main-message-input textarea {
                border: 2px solid #ddd !important;
                border-radius: 8px !important;
                font-size: 14px !important;
            }
            .main-message-input textarea:focus {
                border-color: #0066cc !important;
                box-shadow: 0 0 5px rgba(0,102,204,0.3) !important;
            }
            </style>
            
            <script>
            // More targeted approach - run after this specific element loads
            setTimeout(function() {
                const messageInput = document.querySelector('textarea[aria-label="main_message_input"]') ||
                                   document.querySelector('#main_message_input textarea') ||
                                   document.querySelector('.main-message-input textarea') ||
                                   document.querySelector('textarea[placeholder*="Ask me anything"]');
                
                if (messageInput && !messageInput.hasAttribute('data-enter-setup')) {
                    messageInput.setAttribute('data-enter-setup', 'true');
                    messageInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            const submitBtn = document.querySelector('button[kind="primaryFormSubmit"]') ||
                                            document.querySelector('.stFormSubmitButton button');
                            if (submitBtn) submitBtn.click();
                        }
                    });
                    console.log('Enter key handler attached successfully');
                }
            }, 300);
            </script>
            """, unsafe_allow_html=True)
            
            col_input, col_send = st.columns([4, 1])
            
            with col_input:
                # Use selected question as default value
                user_message = st.text_area(
                    "Type your message...", 
                    placeholder="Ask me anything - documents, weather, general questions!\n\n💡 Tip: Press Enter to send, Shift+Enter for new line",
                    height=80,  # Slightly smaller for fixed position
                    value=selected_question or "",
                    label_visibility="collapsed",
                    key="main_message_input",
                    help="💡 Press Enter to send • Shift+Enter for new line"
                )
            
            with col_send:
                send_button = st.form_submit_button("🚀 Send", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle message sending
        if send_button and user_message:
            # Clear selected question when sending
            if selected_question:
                SessionManager.set("selected_question", None)
            
            if not user_id:
                st.error("❌ Please start a new session first by clicking '🚀 Start New Session' in the sidebar.")
                st.stop()
                
            current_chat_id = SessionManager.get("current_chat_id")
            
            with st.spinner("🤔 AI is thinking..."):
                # Always use the intelligent orchestrator for all questions
                try:
                    response = chatbot.send_message(
                        user_id, 
                        user_message,
                        context={"chat_id": current_chat_id} if current_chat_id else None
                    )
                    
                    # Handle orchestrator response format (now includes database storage)
                    if response and response.get("messages"):
                        # For NEW chats: extract and store the chat_id from the backend
                        if not current_chat_id:
                            # This is a new chat - refresh chats and find the newest one
                            chats = chatbot.get_chat_collection(user_id)
                            if chats:
                                # Sort by creation date to get the newest chat
                                newest_chat = max(chats, key=lambda x: x.get('creation', ''))
                                new_chat_id = newest_chat.get('chatId')
                                if new_chat_id:
                                    SessionManager.set("current_chat_id", new_chat_id)
                                    
                                    # Load messages from the database for this chat
                                    chat_messages = chatbot.get_chat_messages(new_chat_id)
                                    SessionManager.set("messages", chat_messages or [])
                                else:
                                    # Fallback: use response messages if we can't find the chat_id
                                    new_messages = response["messages"]
                                    SessionManager.set("messages", new_messages)
                            else:
                                # Fallback: use response messages if no chats found
                                new_messages = response["messages"]
                                SessionManager.set("messages", new_messages)
                        else:
                            # Existing chat: reload all messages to get the latest
                            chat_messages = chatbot.get_chat_messages(current_chat_id)
                            SessionManager.set("messages", chat_messages or [])
                        
                        # Refresh chats in sidebar to show the new/updated chat
                        chats = chatbot.get_chat_collection(user_id)
                        SessionManager.set("chats", chats)
                        
                        st.rerun()
                        
                    elif response:
                        st.error(f"❌ Backend error: {response.get('message', 'Unknown error')}")
                    else:
                        st.error("❌ No response from server. Please check if the backend is running.")
                        
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
        
        # with col2:
            # Stats and info panel
            # st.markdown("### 📊 Session Info")
            
            # # Session stats
            # messages = SessionManager.get("messages", [])
            # chats = SessionManager.get("chats", [])
            # st.markdown(f"""
            # <div class="stats-container">
            #     <h4>📈 Statistics</h4>
            #     <p><strong>💬 Messages:</strong> {len(messages)}</p>
            #     <p><strong>🗂️ Total Chats:</strong> {len(chats)}</p>
            #     <p><strong>👤 User ID:</strong> {user_id[:8] if user_id else 'None'}...</p>
            # </div>
            # """, unsafe_allow_html=True)
            
            # # Current chat info
            # current_chat_id = SessionManager.get("current_chat_id")
            # if current_chat_id:
            #     st.success(f"💬 Active Chat: {current_chat_id[:8]}...")
                
            #     # Show current chat title if available
            #     chats = SessionManager.get("chats", [])
            #     current_chat = next((c for c in chats if c.get("chatId") == current_chat_id), None)
            #     if current_chat:
            #         chat_title = current_chat.get("chatTitle", "Untitled Chat")
            #         st.caption(f"📝 {chat_title[:30]}{'...' if len(chat_title) > 30 else ''}")
            # else:
            #     st.info("💬 No Active Chat")
            
            # # Quick tips
            # st.markdown("### 💡 Quick Tips")
            # st.markdown("""
            # - Upload documents to get AI insights
            # - Ask specific questions about your content
            # - Use natural language queries
            # - Check sources in AI responses
            # - Start new chats for different topics
            # - **NEW:** Click ✏️ to edit your messages!
            # """)
            
            # # API Status
            # try:
            #     health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            #     if health_response.status_code == 200:
            #         st.success("🟢 API Online")
            #     else:
            #         st.error("🔴 API Issues")
            # except:
            #     st.error("🔴 API Offline")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🤖 AI Document Chat Assistant | Built with Streamlit & FastAPI | 
        <a href="http://127.0.0.1:8011/docs" target="_blank">API Docs</a>
    </div>
    """, unsafe_allow_html=True)


# Entry point logic
if __name__ == "__main__":
    # When running: python main.py
    current_file = os.path.abspath(__file__)
    
    print("🚀 Starting AI Document Chat Assistant Frontend...")
    print("📱 Local URL: http://localhost:8511")
    print("📱 Network URL: http://10.224.85.13:8511")
    print("⚡ Press Ctrl+C to stop the server\n")
    
    try:
        # Start streamlit server
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", current_file,
            "--server.port", "8511",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped!")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        print("💡 Make sure streamlit is installed: pip install streamlit")

# This will be called when Streamlit runs this file
run_streamlit_app()
