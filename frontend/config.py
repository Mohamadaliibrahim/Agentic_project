"""
Configuration file for the Streamlit frontend
"""

import os

class Config:
    # API Configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8011")
    
    # Streamlit Configuration
    PAGE_TITLE = "🤖 AI Document Chat Assistant"
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    
    # UI Configuration
    MAX_MESSAGE_LENGTH = 1000
    MAX_FILE_SIZE_MB = 10
    SUPPORTED_FILE_TYPES = ['pdf', 'txt', 'csv', 'docx']
    
    # Colors and Styling
    PRIMARY_COLOR = "#667eea"
    SECONDARY_COLOR = "#764ba2"
    BACKGROUND_COLOR = "#fafafa"
    
    # Chat Configuration
    MAX_MESSAGES_DISPLAY = 50
    MESSAGE_REFRESH_INTERVAL = 1

config = Config()
