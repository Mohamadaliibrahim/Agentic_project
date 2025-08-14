"""
Utility functions for the Streamlit frontend
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def validate_api_response(response: requests.Response) -> bool:
    """Validate API response"""
    try:
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return False

def safe_json_loads(json_str: str, default=None):
    """Safely load JSON string"""
    try:
        return json.loads(json_str)
    except:
        return default

def create_download_link(data: str, filename: str, text: str = "Download"):
    """Create a download link for data"""
    import base64
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">{text}</a>'
    return href

def show_loading_animation():
    """Show a loading animation"""
    return st.spinner("🤔 Processing...")

def show_success_message(message: str):
    """Show a success message with custom styling"""
    st.success(f"✅ {message}")

def show_error_message(message: str):
    """Show an error message with custom styling"""
    st.error(f"❌ {message}")

def show_info_message(message: str):
    """Show an info message with custom styling"""
    st.info(f"ℹ️ {message}")

def create_chat_bubble(message: Dict[str, Any], is_user: bool = True) -> str:
    """Create HTML for chat bubble"""
    message_class = "user-message" if is_user else "assistant-message"
    icon = "👤" if is_user else "🤖"
    sender = "You" if is_user else "Assistant"
    
    sources_html = ""
    if not is_user and message.get("sources"):
        sources_html = "<br><strong>📚 Sources:</strong><br>"
        for source in message["sources"]:
            relevance = source.get('relevance_score', 0)
            doc_name = source.get('document', 'Unknown')
            sources_html += f"""
            <span class="source-chip">
                📄 {doc_name} (Score: {relevance:.2f})
            </span>
            """
    
    timestamp = format_timestamp(message.get("timestamp", ""))
    
    return f"""
    <div class="chat-message {message_class}">
        <strong>{icon} {sender}:</strong><br>
        {message.get("content", "")}
        {sources_html}
        <small style="color: #666; float: right;">
            {timestamp}
        </small>
    </div>
    """

def get_system_stats() -> Dict[str, Any]:
    """Get system statistics"""
    import psutil
    import platform
    
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if platform.system() != "Windows" else psutil.disk_usage('C:').percent
    }

def check_api_health(api_url: str) -> bool:
    """Check if API is healthy"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

class SessionManager:
    """Manage Streamlit session state"""
    
    @staticmethod
    def init_session():
        """Initialize session state variables"""
        default_values = {
            "user_id": None,
            "current_chat_id": None,
            "messages": [],
            "chats": [],
            "documents": [],
            "last_refresh": None,
            "api_status": "unknown"
        }
        
        for key, value in default_values.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def reset_session():
        """Reset session state"""
        for key in ["user_id", "current_chat_id", "messages", "chats", "documents"]:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def get(key: str, default=None):
        """Get session state value"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value):
        """Set session state value"""
        st.session_state[key] = value
    
    @staticmethod
    def update(updates: Dict[str, Any]):
        """Update multiple session state values"""
        for key, value in updates.items():
            st.session_state[key] = value
