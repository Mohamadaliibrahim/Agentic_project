"""
New Tool-Based Orchestrator
Uses the bot_tools system with proper tool calling workflow:
1. Orchestrator identifies which tool to use
2. Calls the tool and gets raw data
3. Sends tool data + prompt to LLM
4. LLM formats the response for the user
"""

import asyncio
import json
import logging
import uuid
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import the bot tools directly
from .bot_tools.weather_tool import WeatherTool
from .bot_tools.rag_tool import RAGTool

# Import services
# Import services from the same module
try:
    from .mistral_service import mistral_service
except ImportError:
    mistral_service = None

try:
    from .logger import app_logger
except ImportError:
    app_logger = None

logger = logging.getLogger(__name__)

@dataclass
class OrchestrationRequest:
    """Request structure for orchestration"""
    user_input: str
    user_id: str
    context: Dict[str, Any] = None

@dataclass
class OrchestrationResponse:
    """Response from orchestration"""
    success: bool
    response: str
    tool_used: Optional[str] = None
    metadata: Dict[str, Any] = None
    execution_time: float = 0.0

class ToolBasedOrchestrator:
    """
    Orchestrator that uses bot tools with LLM integration
    """
    
    def __init__(self):
        # Initialize available tools
        self.tools = {
            "weather_query": WeatherTool(),
            "rag_search": RAGTool(),
        }
        self.logger = logger
        
    async def process_request(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """
        Main orchestration method following the new workflow:
        1. Identify appropriate tool
        2. Execute tool to get raw data
        3. Send data + prompt to LLM for formatting
        4. Return formatted response
        """
        import time
        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]
        
        # Log the incoming request
        if app_logger:
            app_logger.log_prompt(
                session_id=session_id,
                prompt_content=f"USER_INPUT: {request.user_input}",
                response_content="[Processing with tool system...]",
                prompt_type="orchestrator_request"
            )
        
        try:
            self.logger.info(f"[{session_id}] Processing request: {request.user_input[:100]}...")
            
            # Step 1: Identify the appropriate tool
            selected_tool_name = await self._identify_tool(request.user_input)
            
            if not selected_tool_name:
                # Fallback to general conversation
                return await self._handle_general_conversation(request, session_id)
            
            # Step 2: Get the tool and execute it
            tool = self.tools.get(selected_tool_name)
            if not tool:
                self.logger.error(f"Tool '{selected_tool_name}' not found")
                return await self._handle_general_conversation(request, session_id)
            
            self.logger.info(f"[{session_id}] Using tool: {selected_tool_name}")
            
            # Extract parameters for the tool
            parameters = await self._extract_tool_parameters(tool, request.user_input, request.user_id)
            
            # Execute the tool
            tool_response = await tool.execute(parameters)
            
            if not tool_response.success:
                self.logger.warning(f"[{session_id}] Tool execution failed: {tool_response.error}")
                # Log the failure
                if app_logger:
                    app_logger.log_prompt(
                        session_id=session_id,
                        prompt_content=f"USER_INPUT: {request.user_input}",
                        response_content=f"TOOL_ERROR: {selected_tool_name} failed - {tool_response.error}",
                        prompt_type="tool_execution_error"
                    )
                return await self._handle_general_conversation(request, session_id)
            
            # Step 3: Format the prompt for LLM using tool results
            llm_prompt = tool.format_llm_prompt(tool_response, request.user_input)
            
            # Log the tool execution and prompt
            if app_logger:
                app_logger.log_prompt(
                    session_id=session_id,
                    prompt_content=f"TOOL_EXECUTION: {selected_tool_name} | PARAMETERS: {parameters}",
                    response_content=f"TOOL_DATA: {tool_response.data}",
                    prompt_type="tool_execution_success"
                )
            
            # Step 4: Send to LLM for final formatting
            if mistral_service:
                formatted_response = await mistral_service.generate_response(
                    user_message=llm_prompt,
                    user_id=request.user_id,
                    conversation_history=request.context.get("conversation_history", []) if request.context else []
                )
                
                # Log the final LLM response
                if app_logger:
                    app_logger.log_prompt(
                        session_id=session_id,
                        prompt_content=llm_prompt[:200] + "...",
                        response_content=formatted_response,
                        prompt_type="final_llm_response"
                    )
                
            else:
                # Fallback if Mistral service is not available
                formatted_response = f"Tool executed successfully but LLM formatting unavailable. Raw data: {tool_response.data}"
            
            execution_time = time.time() - start_time
            
            return OrchestrationResponse(
                success=True,
                response=formatted_response,
                tool_used=selected_tool_name,
                metadata={
                    "session_id": session_id,
                    "tool_metadata": tool_response.metadata,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"[{session_id}] Orchestration failed: {str(e)}")
            
            # Log the error
            if app_logger:
                app_logger.log_prompt(
                    session_id=session_id,
                    prompt_content=f"USER_INPUT: {request.user_input}",
                    response_content=f"ORCHESTRATION_ERROR: {str(e)}",
                    prompt_type="orchestration_error"
                )
            
            execution_time = time.time() - start_time
            
            return OrchestrationResponse(
                success=False,
                response="I encountered an unexpected error while processing your request. Please try again.",
                metadata={"error": str(e), "session_id": session_id},
                execution_time=execution_time
            )
    
    async def _identify_tool(self, user_input: str) -> Optional[str]:
        """
        Identify which tool should handle the user input
        Uses pattern matching for now, could be enhanced with LLM classification
        """
        user_input_lower = user_input.lower()
        
        # Weather detection
        weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "climate"]
        if any(keyword in user_input_lower for keyword in weather_keywords):
            return "weather_query"
        

        
        # Default to RAG search for document-related queries
        # This will be the most common fallback
        return "rag_search"
    
    async def _extract_tool_parameters(self, tool, user_input: str, user_id: str) -> Dict[str, Any]:
        """Extract parameters needed for the specific tool"""
        
        if tool.tool_name == "weather_query":
            # Extract location from weather query
            location = tool.extract_location_from_query(user_input)
            return {"location": location}
            
        elif tool.tool_name == "rag_search":
            # For RAG, use the full query and user ID
            return {"query": user_input, "user_id": user_id}
            
        else:
            # Generic parameter extraction
            return {"query": user_input, "user_id": user_id}
    
    def _extract_shipment_id(self, user_input: str) -> str:
        """Extract shipment/booking ID from user input"""
        # Look for patterns like CMA123456, BOOKING123, etc.
        patterns = [
            r"(CMA[A-Z]*\d+[A-Z0-9]*)",
            r"(BOOKING[A-Z]*\d+[A-Z0-9]*)",
            r"(SHIPMENT[A-Z]*\d+[A-Z0-9]*)",
            r"([A-Z]{3,4}\d{7,})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input.upper())
            if match:
                return match.group(1)
        
        # If no pattern found, return a placeholder or ask user
        return "UNKNOWN_SHIPMENT_ID"
    
    async def _handle_general_conversation(self, request: OrchestrationRequest, session_id: str) -> OrchestrationResponse:
        """Handle general conversation when no specific tool is identified"""
        
        if mistral_service:
            conversation_prompt = f"""You are a helpful AI assistant for CMA CGM shipping and logistics. 

The user said: "{request.user_input}"

This doesn't seem to match any of our specific tools (weather, document search, shipment tracking), so please provide a helpful general response. 

If the user is asking about:
- Weather: Ask them to specify a location
- Shipping/logistics: Ask for specific shipment or booking numbers
- Document questions: Let them know they can upload documents for search
- General questions: Answer helpfully based on your knowledge

Be friendly and guide them toward using the specific tools when appropriate."""

            response = await mistral_service.generate_response(
                user_message=conversation_prompt,
                user_id=request.user_id,
                conversation_history=request.context.get("conversation_history", []) if request.context else []
            )
        else:
            response = "I'm a CMA CGM assistant. I can help with weather queries, document searches, and shipment tracking. How can I assist you today?"
        
        # Log the general conversation
        if app_logger:
            app_logger.log_prompt(
                session_id=session_id,
                prompt_content=f"USER_INPUT: {request.user_input}",
                response_content=f"GENERAL_CONVERSATION: {response}",
                prompt_type="general_conversation"
            )
        
        return OrchestrationResponse(
            success=True,
            response=response,
            tool_used="general_conversation",
            metadata={"type": "fallback", "session_id": session_id}
        )

# Create instance
orchestrator = ToolBasedOrchestrator()