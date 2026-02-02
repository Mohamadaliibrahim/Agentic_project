"""
Base Tool Class
Defines the interface and structure for all bot tools
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json

@dataclass
class ToolSchema:
    """Tool schema definition following OpenAI function calling format"""
    type: str = "function"
    function: Dict[str, Any] = None

@dataclass 
class ToolResponse:
    """Response from a tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class BaseBotTool(ABC):
    """Abstract base class for all bot tools"""
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the unique name of this tool"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this tool does"""
        pass
    
    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """Return the parameters schema for this tool"""
        pass
    
    @property
    @abstractmethod
    def llm_prompt_template(self) -> str:
        """Return the prompt template to send to LLM with tool results"""
        pass
    
    def get_schema(self) -> ToolSchema:
        """Get the complete tool schema in OpenAI format"""
        return ToolSchema(
            type="function",
            function={
                "name": self.tool_name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        )
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Execute the tool with given parameters"""
        pass
    
    def format_llm_prompt(self, tool_response: ToolResponse, user_query: str) -> str:
        """Format the prompt to send to LLM with tool results"""
        if not tool_response.success:
            return f"""The user asked: "{user_query}"

I tried to help but encountered an error: {tool_response.error}

Please provide a helpful response explaining that there was an issue and suggest what the user can try instead.
If there is no useful information to provide, simply respond with "I'm sorry, I couldn't retrieve the information you requested."""

        return self.llm_prompt_template.format(
            user_query=user_query,
            tool_data=tool_response.data,
            metadata=tool_response.metadata or {}
        )