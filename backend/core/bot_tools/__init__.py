"""
Bot Tools Module
Contains all the individual tools that can be called by the orchestrator
"""

from .base_tool import BaseBotTool
from .weather_tool import WeatherTool
from .rag_tool import RAGTool

# Registry of all available tools
AVAILABLE_TOOLS = {
    "weather_query": WeatherTool(),
    "rag_search": RAGTool(),
}

def get_tool(tool_name: str) -> BaseBotTool:
    """Get a tool by name"""
    return AVAILABLE_TOOLS.get(tool_name)

def get_all_tools() -> dict:
    """Get all available tools"""
    return AVAILABLE_TOOLS

def get_tool_schemas() -> dict:
    """Get JSON schemas for all tools as a dictionary"""
    return {name: tool.get_schema() for name, tool in AVAILABLE_TOOLS.items()}