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

# Import prompt loader
from .prompt_loader import prompt_loader

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
        Use LLM to intelligently identify which tool should handle the user input
        Returns None if the question is outside the scope of available tools
        """
        if not mistral_service:
            # Fallback to None if Mistral service unavailable
            return None
        
        # Load the tool selection prompt from prompts.txt
        tool_selection_prompt = prompt_loader.get_prompt(
            "main_prompt",
            user_input=user_input
        )
        
        if not tool_selection_prompt:
            self.logger.error("Failed to load main_prompt from prompts.txt")
            return None

        try:
            # Get LLM decision
            llm_response = await mistral_service.generate_response(
                user_message=tool_selection_prompt,
                user_id="system_tool_selector",
                conversation_history=[]
            )
            
            # Clean up the response and extract tool name
            tool_choice = llm_response.strip().lower()
            
            # Validate the response
            if "weather_query" in tool_choice or "weather" in tool_choice:
                self.logger.info(f"LLM selected tool: weather_query")
                return "weather_query"
            elif "rag_search" in tool_choice or "rag" in tool_choice:
                self.logger.info(f"LLM selected tool: rag_search")
                return "rag_search"
            elif "none" in tool_choice:
                self.logger.info(f"LLM determined no tool is applicable")
                return None
            else:
                # If LLM response is unclear, default to None (safer)
                self.logger.warning(f"LLM tool selection unclear: {llm_response}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in LLM tool selection: {str(e)}")
            # On error, return None to trigger "I don't know" response
            return None
    
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
        """
        Handle queries that don't match any available tools
        Use LLM with conversation history for general chat, memory questions, etc.
        """
        
        if not mistral_service:
            response = "I'm sorry, but I'm currently unable to process general conversations."
            return OrchestrationResponse(
                success=True,
                response=response,
                tool_used="general_chat_unavailable",
                metadata={"type": "no_llm_service", "session_id": session_id}
            )
        
        # Get conversation history from context
        conversation_history = []
        if request.context and "conversation_history" in request.context:
            conversation_history = request.context["conversation_history"]
        
        try:
            # Use LLM for general conversation with history
            # The mistral service has a built-in system message that handles conversation context
            response = await mistral_service.generate_response(
                user_message=request.user_input,
                user_id=request.user_id,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            # Log the general conversation
            if app_logger:
                app_logger.log_prompt(
                    session_id=session_id,
                    prompt_content=f"GENERAL_CHAT: {request.user_input}",
                    response_content=response,
                    prompt_type="general_conversation"
                )
            
            return OrchestrationResponse(
                success=True,
                response=response,
                tool_used="general_chat",
                metadata={"type": "general_conversation", "session_id": session_id}
            )
            
        except Exception as e:
            self.logger.error(f"[{session_id}] General conversation failed: {str(e)}")
            
            fallback_response = "I encountered an error while processing your message. Please try rephrasing your question."
            
            return OrchestrationResponse(
                success=True,
                response=fallback_response,
                tool_used="general_chat_error",
                metadata={"error": str(e), "session_id": session_id}
            )

# Create instance
orchestrator = ToolBasedOrchestrator()