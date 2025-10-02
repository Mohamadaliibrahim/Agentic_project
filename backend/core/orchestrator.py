"""
Tool Orchestrator
Intelligently routes requests to appropriate tools/services based on user intent
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Import services with error handling to avoid circular imports
try:
    from core.mistral_service import mistral_service
except ImportError:
    mistral_service = None

try:
    from core.document_processor import document_processor
except ImportError:
    document_processor = None

try:
    from core.embedding_service import embedding_service
except ImportError:
    embedding_service = None

try:
    from core.rag_service import rag_service
except ImportError:
    rag_service = None

try:
    from database.factory import get_db
except ImportError:
    get_db = None

logger = logging.getLogger(__name__)

class ToolType(Enum):
    """Available tool types"""
    SEMANTIC_SEARCH = "semantic_search"
    WEATHER = "weather"
    DOCUMENT_UPLOAD = "document_upload"
    CHAT_CONVERSATION = "chat_conversation"
    EMBEDDING_GENERATION = "embedding_generation"
    DATABASE_QUERY = "database_query"
    FILE_ANALYSIS = "file_analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"

@dataclass
class ToolRequest:
    """Request structure for tool execution"""
    user_input: str
    user_id: str
    context: Dict[str, Any] = None
    files: List[Any] = None
    parameters: Dict[str, Any] = None

@dataclass
class ToolResponse:
    """Response structure from tool execution"""
    success: bool
    tool_used: ToolType
    result: Any
    message: str
    metadata: Dict[str, Any] = None
    execution_time: float = 0.0

class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    @abstractmethod
    async def can_handle(self, request: ToolRequest) -> float:
        """
        Determine if this tool can handle the request
        Returns confidence score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute the tool with the given request"""
        pass
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """Return the tool type"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return tool description"""
        pass

class SemanticSearchTool(BaseTool):
    """Tool for semantic search through uploaded documents"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.SEMANTIC_SEARCH
    
    @property
    def description(self) -> str:
        return "Semantic search through uploaded documents using RAG (Retrieval-Augmented Generation)"
    
    async def can_handle(self, request: ToolRequest) -> float:
        """Check if request is asking for semantic search"""
        user_input = request.user_input.lower()
        
        search_keywords = [
            "search", "find", "look for", "document", "file", "pdf", 
            "what does", "tell me about", "information about", "explain",
            "content", "extract", "retrieve", "semantic", "meaning", "similar"
        ]
        
        confidence = 0.0
        for keyword in search_keywords:
            if keyword in user_input:
                confidence += 0.2
        
        # Higher confidence if asking questions about content
        if any(word in user_input for word in ["what", "how", "why", "where", "when"]):
            confidence += 0.3
            
        return min(confidence, 1.0)
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute semantic search using RAG"""
        try:
            import time
            start_time = time.time()
            
            if rag_service is None:
                return ToolResponse(
                    success=False,
                    tool_used=self.tool_type,
                    result=None,
                    message="RAG service is not available. Please check your configuration."
                )
            
            # Use RAG service to search documents
            response = await rag_service.query_documents(
                query=request.user_input,
                user_id=request.user_id,
                session_id="orchestrator_session"
            )
            
            execution_time = time.time() - start_time
            
            # Extract the answer from the RAG response
            result = response.get("answer", "No answer found in documents")
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result=result,
                message="Semantic search completed successfully",
                metadata={
                    "query": request.user_input,
                    "search_method": "RAG",
                    "search_type": "semantic",
                    "context_used": response.get("context_used", 0),
                    "source_chunks": len(response.get("source_chunks", []))
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=self.tool_type,
                result=None,
                message=f"Semantic search failed: {str(e)}"
            )

class WeatherTool(BaseTool):
    """Tool for getting weather information"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.WEATHER
    
    @property
    def description(self) -> str:
        return "Get current weather information for any location"
    
    async def can_handle(self, request: ToolRequest) -> float:
        """Check if request is asking for weather information"""
        user_input = request.user_input.lower()
        
        weather_keywords = [
            "weather", "temperature", "forecast", "climate", "rain", "sunny",
            "cloudy", "snow", "wind", "humidity", "what's the weather",
            "how's the weather", "weather like", "degrees", "celsius", "fahrenheit"
        ]
        
        confidence = 0.0
        for keyword in weather_keywords:
            if keyword in user_input:
                confidence += 0.4
        
        # Higher confidence if asking about specific locations
        location_indicators = ["in", "at", "for", "city", "country"]
        if any(indicator in user_input for indicator in location_indicators):
            confidence += 0.2
            
        return min(confidence, 1.0)
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute weather query"""
        try:
            import time
            import re
            start_time = time.time()
            
            # Extract location from user input
            user_input = request.user_input.lower()
            
            # Simple location extraction patterns
            location_patterns = [
                r"weather (?:in|at|for) ([a-zA-Z\s]+)",
                r"temperature (?:in|at|for) ([a-zA-Z\s]+)",
                r"(?:in|at|for) ([a-zA-Z\s]+) weather",
                r"weather (?:like )?(?:in|at) ([a-zA-Z\s]+)",
            ]
            
            location = "current location"
            for pattern in location_patterns:
                match = re.search(pattern, user_input)
                if match:
                    location = match.group(1).strip()
                    break
            
            # Mock weather data (replace with real API call)
            weather_data = await self._get_weather_data(location)
            
            execution_time = time.time() - start_time
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result=weather_data,
                message=f"Weather information retrieved for {location}",
                metadata={
                    "location": location,
                    "query": request.user_input,
                    "weather_source": "mock_api"
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Weather query failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=self.tool_type,
                result=None,
                message=f"Weather query failed: {str(e)}"
            )
    
    async def _get_weather_data(self, location: str) -> str:
        """
        Get weather data for a location
        This is a mock implementation - replace with real weather API
        """
        import random
        
        # Mock weather conditions
        conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "overcast"]
        temperatures = list(range(15, 35))  # Celsius
        
        condition = random.choice(conditions)
        temp = random.choice(temperatures)
        humidity = random.randint(30, 80)
        wind_speed = random.randint(5, 25)
        
        weather_report = f"""🌤️ Weather Report for {location.title()}:
        
📍 Location: {location.title()}
🌡️ Temperature: {temp}°C ({temp * 9/5 + 32:.0f}°F)
☁️ Condition: {condition.title()}
💧 Humidity: {humidity}%
💨 Wind Speed: {wind_speed} km/h

Note: This is simulated weather data. For real weather information, integrate with a weather API like OpenWeatherMap, WeatherAPI, or similar service."""
        
        return weather_report

class ChatConversationTool(BaseTool):
    """Tool for general conversation using Mistral AI"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.CHAT_CONVERSATION
    
    @property
    def description(self) -> str:
        return "General conversation and question answering using Mistral AI"
    
    async def can_handle(self, request: ToolRequest) -> float:
        """Check if request is general conversation"""
        user_input = request.user_input.lower()
        
        # Lower confidence for general chat - this should be fallback
        conversation_indicators = [
            "hello", "hi", "how are you", "thank you", "thanks",
            "help me", "can you", "please", "explain", "tell me"
        ]
        
        confidence = 0.1  # Base confidence
        
        for indicator in conversation_indicators:
            if indicator in user_input:
                confidence += 0.2
        
        # Don't handle if it's clearly document-related
        document_keywords = ["document", "file", "pdf", "upload", "search"]
        if any(keyword in user_input for keyword in document_keywords):
            confidence *= 0.5
            
        return min(confidence, 0.7)  # Cap at 0.7 so other tools can take precedence
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute general conversation"""
        try:
            import time
            start_time = time.time()
            
            if mistral_service is None:
                return ToolResponse(
                    success=False,
                    tool_used=self.tool_type,
                    result=None,
                    message="Mistral service is not available. Please check your API configuration."
                )
            
            response = await mistral_service.generate_response(
                user_message=request.user_input,
                user_id=request.user_id,
                conversation_history=request.context.get("conversation_history", []) if request.context else []
            )
            
            execution_time = time.time() - start_time
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result=response,
                message="Conversation completed successfully",
                metadata={
                    "model": "mistral-ai",
                    "conversation_type": "general"
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Chat conversation failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=self.tool_type,
                result=None,
                message=f"Chat conversation failed: {str(e)}"
            )

class DocumentAnalysisTool(BaseTool):
    """Tool for analyzing document content and structure"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.FILE_ANALYSIS
    
    @property
    def description(self) -> str:
        return "Analyze document structure, content, and provide insights"
    
    async def can_handle(self, request: ToolRequest) -> float:
        """Check if request is asking for document analysis"""
        user_input = request.user_input.lower()
        
        analysis_keywords = [
            "analyze", "analysis", "structure", "content", "insights",
            "breakdown", "examine", "review", "assess", "evaluate"
        ]
        
        confidence = 0.0
        for keyword in analysis_keywords:
            if keyword in user_input:
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute document analysis"""
        try:
            import time
            start_time = time.time()
            
            db = get_db()
            user_documents = await db.get_user_documents(request.user_id)
            
            if not user_documents:
                return ToolResponse(
                    success=False,
                    tool_used=self.tool_type,
                    result=None,
                    message="No documents found for analysis. Please upload documents first."
                )
            
            # Analyze documents
            analysis_results = []
            for doc in user_documents:
                analysis = {
                    "filename": doc["filename"],
                    "file_type": doc["file_type"],
                    "total_chunks": doc["total_chunks"],
                    "upload_date": str(doc["upload_date"]),
                    "file_size": doc.get("file_size", 0)
                }
                analysis_results.append(analysis)
            
            execution_time = time.time() - start_time
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result={
                    "total_documents": len(user_documents),
                    "documents": analysis_results,
                    "summary": f"Found {len(user_documents)} documents with a total of {sum(doc['total_chunks'] for doc in user_documents)} chunks"
                },
                message="Document analysis completed successfully",
                metadata={
                    "analysis_type": "document_overview"
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=self.tool_type,
                result=None,
                message=f"Document analysis failed: {str(e)}"
            )

class SummarizationTool(BaseTool):
    """Tool for summarizing content"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.SUMMARIZATION
    
    @property
    def description(self) -> str:
        return "Summarize documents or text content"
    
    async def can_handle(self, request: ToolRequest) -> float:
        """Check if request is asking for summarization"""
        user_input = request.user_input.lower()
        
        summary_keywords = [
            "summarize", "summary", "brief", "overview", "highlights",
            "key points", "main points", "tldr", "condense"
        ]
        
        confidence = 0.0
        for keyword in summary_keywords:
            if keyword in user_input:
                confidence += 0.4
        
        return min(confidence, 1.0)
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute summarization"""
        try:
            import time
            start_time = time.time()
            
            if rag_service is None:
                return ToolResponse(
                    success=False,
                    tool_used=self.tool_type,
                    result=None,
                    message="RAG service is not available. Please check your configuration."
                )
            
            # Create a summarization prompt
            summary_prompt = f"Please provide a comprehensive summary of the following request and any relevant documents: {request.user_input}"
            
            response = await rag_service.query_documents(
                query=summary_prompt,
                user_id=request.user_id,
                session_id="summarization_session"
            )
            
            execution_time = time.time() - start_time
            
            # Extract the answer from the RAG response
            result = response.get("answer", "No documents found to summarize")
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result=result,
                message="Summarization completed successfully",
                metadata={
                    "summary_type": "document_based",
                    "context_used": response.get("context_used", 0),
                    "source_chunks": len(response.get("source_chunks", []))
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=self.tool_type,
                result=None,
                message=f"Summarization failed: {str(e)}"
            )

class ToolOrchestrator:
    """
    Main orchestrator that routes requests to appropriate tools
    """
    
    def __init__(self):
        self.tools: List[BaseTool] = [
            SemanticSearchTool(),
            WeatherTool(),
            SummarizationTool(),
            DocumentAnalysisTool(),
            ChatConversationTool()  # Keep this last as fallback
        ]
        self.logger = logging.getLogger("tool_orchestrator")
    
    async def analyze_intent(self, request: ToolRequest) -> Dict[ToolType, float]:
        """
        Analyze user intent and return confidence scores for each tool
        """
        tool_scores = {}
        
        for tool in self.tools:
            try:
                score = await tool.can_handle(request)
                tool_scores[tool.tool_type] = score
                self.logger.debug(f"Tool {tool.tool_type.value} confidence: {score}")
            except Exception as e:
                self.logger.error(f"Error analyzing intent for {tool.tool_type.value}: {str(e)}")
                tool_scores[tool.tool_type] = 0.0
        
        return tool_scores
    
    async def select_best_tool(self, request: ToolRequest) -> Optional[BaseTool]:
        """
        Select the best tool based on confidence scores
        """
        tool_scores = await self.analyze_intent(request)
        
        if not tool_scores:
            return None
        
        # Find tool with highest confidence
        best_tool_type = max(tool_scores, key=tool_scores.get)
        best_score = tool_scores[best_tool_type]
        
        if best_score < 0.1:  # Minimum confidence threshold
            return None
        
        # Find the corresponding tool instance
        for tool in self.tools:
            if tool.tool_type == best_tool_type:
                return tool
        
        return None
    
    async def execute_request(self, request: ToolRequest) -> ToolResponse:
        """
        Main execution method - analyzes intent and routes to appropriate tool
        """
        try:
            self.logger.info(f"Processing request: {request.user_input[:100]}...")
            
            # Analyze intent and select tool
            selected_tool = await self.select_best_tool(request)
            
            if not selected_tool:
                return ToolResponse(
                    success=False,
                    tool_used=ToolType.CHAT_CONVERSATION,
                    result=None,
                    message="Could not determine appropriate tool for this request. Please be more specific."
                )
            
            self.logger.info(f"Selected tool: {selected_tool.tool_type.value}")
            
            # Execute the selected tool
            response = await selected_tool.execute(request)
            
            self.logger.info(f"Tool execution completed. Success: {response.success}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Orchestrator execution failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=ToolType.CHAT_CONVERSATION,
                result=None,
                message=f"System error occurred: {str(e)}"
            )
    
    def get_available_tools(self) -> Dict[str, str]:
        """
        Get list of available tools and their descriptions
        """
        return {
            tool.tool_type.value: tool.description 
            for tool in self.tools
        }
    
    async def get_tool_suggestions(self, request: ToolRequest) -> List[Dict[str, Any]]:
        """
        Get suggestions for which tools could handle the request
        """
        tool_scores = await self.analyze_intent(request)
        
        suggestions = []
        for tool in self.tools:
            score = tool_scores.get(tool.tool_type, 0.0)
            if score > 0.1:
                suggestions.append({
                    "tool_type": tool.tool_type.value,
                    "description": tool.description,
                    "confidence": score,
                    "recommended": score > 0.5
                })
        
        # Sort by confidence score
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions

# Global orchestrator instance
orchestrator = ToolOrchestrator()