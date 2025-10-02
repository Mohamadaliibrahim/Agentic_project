"""
Orchestrator Routes
API endpoints for the intelligent tool orchestrator
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.orchestrator import orchestrator, ToolRequest, ToolResponse, ToolType

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for API
class OrchestratorRequest(BaseModel):
    user_input: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None

class OrchestratorResponse(BaseModel):
    success: bool
    tool_used: str
    result: Any
    message: str
    metadata: Optional[Dict[str, Any]] = None
    execution_time: float

class ToolSuggestion(BaseModel):
    tool_type: str
    description: str
    confidence: float
    recommended: bool

class AvailableToolsResponse(BaseModel):
    tools: Dict[str, str]
    total_tools: int

@router.post("/orchestrator/execute", response_model=OrchestratorResponse, tags=["Orchestrator"])
async def execute_orchestrated_request(request: OrchestratorRequest):
    """
    Execute a request using the intelligent tool orchestrator
    
    The orchestrator will:
    1. Analyze the user input to determine intent
    2. Select the most appropriate tool
    3. Execute the tool with the given parameters
    4. Return the results with metadata
    
    Example requests:
    - "Search for information about project management in my documents"
    - "Summarize the main points from the uploaded PDF"
    - "Analyze my documents and tell me what they contain"
    - "Hello, how are you today?"
    """
    try:
        # Create tool request
        tool_request = ToolRequest(
            user_input=request.user_input,
            user_id=request.user_id,
            context=request.context or {},
            parameters=request.parameters or {}
        )
        
        # Execute through orchestrator
        response = await orchestrator.execute_request(tool_request)
        
        return OrchestratorResponse(
            success=response.success,
            tool_used=response.tool_used.value,
            result=response.result,
            message=response.message,
            metadata=response.metadata,
            execution_time=response.execution_time
        )
        
    except Exception as e:
        logger.error(f"Orchestrator execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator execution failed: {str(e)}"
        )

# Add new endpoint for orchestrated chat messages that get saved to database
from data_validation import ChatMessagesResponse, DocumentQueryRequest
from database.factory import get_db
from datetime import datetime
from typing import Optional
from fastapi import Query
import uuid

@router.post("/orchestrator/chat", response_model=ChatMessagesResponse, tags=["Orchestrator"])
async def orchestrated_chat_message(
    request: DocumentQueryRequest,
    chat_id: Optional[str] = Query(None, description="Optional chat ID for continuing existing conversations")
):
    """
    Send a message through the intelligent orchestrator AND save to database
    
    This combines the orchestrator's intelligence with proper message persistence.
    Works exactly like the old /chat/message endpoint but uses orchestrator routing.
    
    Features:
    - Intelligent routing (weather, documents, chat, etc.)  
    - Message persistence in MongoDB
    - Chat history support
    - Proper response formatting for frontend
    """
    try:
        from datetime import datetime
        import uuid
        
        # Generate chat_id if not provided (new conversation)
        if not chat_id:
            chat_id = str(uuid.uuid4())
        
        # Record timestamps
        message_sent_timestamp = datetime.utcnow()
        
        # Create tool request for orchestrator
        tool_request = ToolRequest(
            user_input=request.query,
            user_id=request.user_id,
            context={"chat_id": chat_id} if chat_id else {},
            parameters={}
        )
        
        # Execute through orchestrator
        orchestrator_response = await orchestrator.execute_request(tool_request)
        
        if not orchestrator_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Orchestrator failed: {orchestrator_response.message}"
            )
        
        answer_received_timestamp = datetime.utcnow()
        
        # Save message to database (similar to old chat/message endpoint)
        db = get_db()
        next_message_id = await db.get_next_message_id_for_chat(chat_id)
        
        # Format the result 
        final_answer = str(orchestrator_response.result)
        tool_info = f" [Tool: {orchestrator_response.tool_used}]"
        
        message_data = {
            "message_id": str(next_message_id),
            "user_id": request.user_id,
            "chat_id": chat_id,
            "date": datetime.utcnow(),
            "user_message": request.query,
            "assistant_message": final_answer + tool_info,
            "query_type": f"orchestrator_{orchestrator_response.tool_used}",
            "source_chunks": [],  # Could be populated for semantic_search tool
            "message_sent_timestamp": message_sent_timestamp,
            "answer_received_timestamp": answer_received_timestamp,
            "orchestrator_metadata": orchestrator_response.metadata
        }
        
        # Save message
        await db.create_message(message_data)
        
        # Update/create chat collection
        try:
            existing_collections = await db.get_chat_collections_by_user(request.user_id)
            existing_chat = next((c for c in existing_collections if c.get('chat_id') == chat_id), None)
            
            if existing_chat:
                # Update existing chat - preserve creation_date, update other fields
                chat_collection_data = {
                    "chat_title": request.query[:50] + ("..." if len(request.query) > 50 else ""),
                    "last_message_date": datetime.utcnow(),
                    "message_count": next_message_id,
                    "query_type": f"orchestrator_{orchestrator_response.tool_used}"
                }
                await db.update_chat_collection_item(chat_id, chat_collection_data)
            else:
                # Create new chat collection
                chat_collection_data = {
                    "chat_id": chat_id,
                    "user_id": request.user_id,
                    "chat_title": request.query[:50] + ("..." if len(request.query) > 50 else ""),
                    "creation_date": datetime.utcnow(),
                    "last_message_date": datetime.utcnow(),
                    "message_count": next_message_id,
                    "query_type": f"orchestrator_{orchestrator_response.tool_used}"
                }
                try:
                    await db.store_chat_collection_item(chat_collection_data)
                except Exception as insert_error:
                    # Handle duplicate key error - if chat was created by another request, try to update instead
                    if "E11000" in str(insert_error) and "duplicate key" in str(insert_error):
                        logger.warning(f"Chat collection {chat_id} already exists, attempting to update instead")
                        update_data = {
                            "chat_title": request.query[:50] + ("..." if len(request.query) > 50 else ""),
                            "last_message_date": datetime.utcnow(),
                            "message_count": next_message_id,
                            "query_type": f"orchestrator_{orchestrator_response.tool_used}"
                        }
                        await db.update_chat_collection_item(chat_id, update_data)
                    else:
                        raise insert_error
        except Exception as chat_collection_error:
            logger.error(f"Failed to handle chat collection for {chat_id}: {str(chat_collection_error)}")
            # Don't fail the entire request if chat collection fails - the message was already saved
            pass
        
        # Return response in the format expected by frontend
        from data_validation import ChatMessageItem, SourceChunk
        
        messages = [
            ChatMessageItem(
                content=request.query,
                userType="user",
                timestamp=message_sent_timestamp,
                sources=[]
            ),
            ChatMessageItem(
                content=final_answer,
                userType="bot",
                timestamp=answer_received_timestamp,
                sources=[]
            )
        ]
        
        return ChatMessagesResponse(messages=messages)
        
    except Exception as e:
        logger.error(f"Orchestrated chat message failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrated chat message failed: {str(e)}"
        )

@router.post("/orchestrator/analyze", response_model=List[ToolSuggestion], tags=["Orchestrator"])
async def analyze_request_intent(request: OrchestratorRequest):
    """
    Analyze user input and get tool suggestions without executing
    
    This endpoint helps you understand:
    - Which tools could handle the request
    - Confidence scores for each tool
    - Recommended tools based on the analysis
    
    Useful for debugging and understanding the orchestrator's decision-making process.
    """
    try:
        # Create tool request
        tool_request = ToolRequest(
            user_input=request.user_input,
            user_id=request.user_id,
            context=request.context or {},
            parameters=request.parameters or {}
        )
        
        # Get tool suggestions
        suggestions = await orchestrator.get_tool_suggestions(tool_request)
        
        return [
            ToolSuggestion(
                tool_type=suggestion["tool_type"],
                description=suggestion["description"],
                confidence=suggestion["confidence"],
                recommended=suggestion["recommended"]
            )
            for suggestion in suggestions
        ]
        
    except Exception as e:
        logger.error(f"Intent analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent analysis failed: {str(e)}"
        )

@router.get("/orchestrator/tools", response_model=AvailableToolsResponse, tags=["Orchestrator"])
async def get_available_tools():
    """
    Get list of all available tools and their descriptions
    
    Returns information about:
    - Tool types and their capabilities
    - What each tool is designed to handle
    - Total number of available tools
    """
    try:
        tools = orchestrator.get_available_tools()
        
        return AvailableToolsResponse(
            tools=tools,
            total_tools=len(tools)
        )
        
    except Exception as e:
        logger.error(f"Failed to get available tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available tools: {str(e)}"
        )

@router.post("/orchestrator/chat", response_model=OrchestratorResponse, tags=["Orchestrator"])
async def orchestrated_chat(request: OrchestratorRequest):
    """
    Simplified chat interface using the orchestrator
    
    This is a more user-friendly endpoint for chat applications.
    It automatically handles:
    - Intent detection
    - Tool selection
    - Conversation context
    - Error handling
    
    Perfect for integrating with chat UIs or conversational interfaces.
    """
    try:
        # Enhanced context for better tool selection
        enhanced_context = request.context or {}
        
        # Add conversation metadata if not present
        if "conversation_history" not in enhanced_context:
            enhanced_context["conversation_history"] = []
        
        # Create tool request
        tool_request = ToolRequest(
            user_input=request.user_input,
            user_id=request.user_id,
            context=enhanced_context,
            parameters=request.parameters or {}
        )
        
        # Execute through orchestrator
        response = await orchestrator.execute_request(tool_request)
        
        # Add helpful metadata for chat interfaces
        if response.metadata is None:
            response.metadata = {}
        
        response.metadata.update({
            "chat_mode": True,
            "timestamp": str(__import__("datetime").datetime.now()),
            "user_input_length": len(request.user_input)
        })
        
        return OrchestratorResponse(
            success=response.success,
            tool_used=response.tool_used.value,
            result=response.result,
            message=response.message,
            metadata=response.metadata,
            execution_time=response.execution_time
        )
        
    except Exception as e:
        logger.error(f"Orchestrated chat failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat request failed: {str(e)}"
        )