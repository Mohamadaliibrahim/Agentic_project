"""
API Client for communicating with the FastAPI backend
"""

import requests
import streamlit as st
from typing import Dict, Any, List, Optional, Union
import io
from config import config

class APIClient:
    """Client for interacting with the FastAPI backend"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a request to the API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                try:
                    st.error(error_msg)
                except:
                    print(error_msg)  # Fallback if not in Streamlit context
                return None
                
        except requests.exceptions.ConnectionError:
            error_msg = "🔴 Cannot connect to the backend API. Please make sure the backend server is running."
            try:
                st.error(error_msg)
            except:
                print(error_msg)  # Fallback if not in Streamlit context
            return None
        except requests.exceptions.Timeout:
            error_msg = "⏰ Request timed out. Please try again."
            try:
                st.error(error_msg)
            except:
                print(error_msg)  # Fallback if not in Streamlit context
            return None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            try:
                st.error(error_msg)
            except:
                print(error_msg)  # Fallback if not in Streamlit context
            return None
    
    # User endpoints
    def create_user(self) -> Optional[str]:
        """Create a new user and return user ID"""
        response = self._make_request("POST", "/users")
        return response["id"] if response else None
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        return self._make_request("GET", f"/users/{user_id}")
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            response = self.session.delete(f"{self.base_url}/users/{user_id}")
            return response.status_code == 204
        except:
            return False
    
    # Chat endpoints
    def send_message(self, user_id: str, message: str, chat_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Send a message and get response"""
        payload = {
            "query": message,
            "user_id": user_id
        }
        params = {"chat_id": chat_id} if chat_id else {}
        
        return self._make_request("POST", "/chat/message", json=payload, params=params)
    
    def get_chat_collection(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chats for a user"""
        response = self._make_request("GET", "/chat/message/collection", params={"user_id": user_id})
        return response["chats"] if response else []
    
    def get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific chat"""
        response = self._make_request("GET", f"/chat/message/chat/{chat_id}")
        if not response:
            return []
        
        # Transform ChatMessageResponse format to frontend format
        transformed_messages = []
        for msg in response:
            message_id = msg.get("message_id")
            
            # Add user message
            if msg.get("user_message"):
                transformed_messages.append({
                    "content": msg["user_message"],
                    "user_message": msg["user_message"],
                    "userType": "user",
                    "timestamp": msg.get("date", ""),
                    "message_id": message_id,
                    "sources": []
                })
            
            # Add assistant message
            if msg.get("assistant_message"):
                transformed_messages.append({
                    "content": msg["assistant_message"],
                    "assistant_message": msg["assistant_message"],
                    "userType": "bot",
                    "timestamp": msg.get("date", ""),
                    "message_id": message_id,
                    "sources": []
                })
        
        return transformed_messages
    
    def get_user_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a user"""
        response = self._make_request("GET", f"/chat/message/users/{user_id}")
        return response if response else []
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat and all its messages"""
        try:
            response = self.session.delete(f"{self.base_url}/chat/message/chat/{chat_id}")
            return response.status_code == 200
        except:
            return False
    
    def delete_user_messages(self, user_id: str) -> bool:
        """Delete all messages for a user"""
        try:
            response = self.session.delete(f"{self.base_url}/chat/message/users/{user_id}")
            return response.status_code == 200
        except:
            return False
    
    def update_chat_title(self, chat_id: str, new_title: str) -> Optional[Dict[str, Any]]:
        """Update the title of a chat"""
        payload = {"title": new_title}
        return self._make_request("PUT", f"/chat/message/chat/{chat_id}/title", json=payload)
    
    def update_message(self, message_id: str, new_user_message: str) -> Optional[Dict[str, Any]]:
        """Update a message content"""
        payload = {"user_message": new_user_message}
        return self._make_request("PUT", f"/chat/message/{message_id}", json=payload)
    
    def update_message_and_regenerate(self, message_id: str, new_user_message: str) -> Optional[Dict[str, Any]]:
        """Update a message content and regenerate AI response"""
        payload = {"user_message": new_user_message}
        return self._make_request("PUT", f"/chat/message/{message_id}/regenerate", json=payload)
    
    # Document endpoints
    def upload_document(self, user_id: str, file) -> Optional[Dict[str, Any]]:
        """Upload a document"""
        try:
            # Prepare file for upload
            if hasattr(file, 'read'):
                file_content = file.read()
                file.seek(0) if hasattr(file, 'seek') else None  # Reset file pointer if possible
                
                # Handle different file content types
                if isinstance(file_content, str):
                    file_content = file_content.encode('utf-8')
                
                files = {"file": (getattr(file, 'name', 'unknown'), io.BytesIO(file_content), getattr(file, 'type', 'application/octet-stream'))}
            else:
                files = {"file": file}
            
            data = {"user_id": user_id}
            
            # Use a fresh requests session without custom headers for file upload
            # The session with "Content-Type: application/json" interferes with multipart/form-data
            response = requests.post(
                f"{self.base_url}/documents/upload",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Upload failed: {response.status_code} - {response.text}"
                try:
                    st.error(error_msg)
                except:
                    print(error_msg)  # Fallback if not in Streamlit context
                return None
                
        except Exception as e:
            error_msg = f"Error uploading document: {str(e)}"
            try:
                st.error(error_msg)
            except:
                print(error_msg)  # Fallback if not in Streamlit context
            return None
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        response = self._make_request("GET", "/documents", params={"user_id": user_id})
        return response if response else []
    
    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific document"""
        return self._make_request("GET", f"/documents/{document_id}")
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            response = self.session.delete(f"{self.base_url}/documents/{document_id}")
            return response.status_code == 200
        except:
            return False
    
    def get_document_chunks(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get chunks for a document (for debugging)"""
        return self._make_request("GET", f"/documents/{document_id}/chunks")
    
    # Health endpoints
    def check_health(self) -> bool:
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_ai_health(self) -> bool:
        """Check if the AI service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/ai-health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """Get API information"""
        return self._make_request("GET", "/")

# Create a singleton instance
api_client = APIClient()
