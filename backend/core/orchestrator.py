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
    
    # Note: can_handle method removed - we now use LLM-based classification
    
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
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute weather query"""
        try:
            import time
            import re
            start_time = time.time()
            
            # Extract location from user input
            user_input = request.user_input.lower()
            
            # Simple location extraction patterns with time exclusion
            location_patterns = [
                r"weather (?:in|at|for) ([a-zA-Z\s]+?)(?:\s+(?:now|today|currently|right\s+now|at\s+the\s+moment|this\s+moment))?(?:\s*[\?\.])?$",
                r"temperature (?:in|at|for) ([a-zA-Z\s]+?)(?:\s+(?:now|today|currently|right\s+now|at\s+the\s+moment|this\s+moment))?(?:\s*[\?\.])?$",
                r"(?:in|at|for) ([a-zA-Z\s]+?)(?:\s+(?:now|today|currently|right\s+now|at\s+the\s+moment|this\s+moment))?\s+weather",
                r"weather (?:like )?(?:in|at) ([a-zA-Z\s]+?)(?:\s+(?:now|today|currently|right\s+now|at\s+the\s+moment|this\s+moment))?(?:\s*[\?\.])?$",
                r"what(?:'s|\s+is)\s+the\s+weather\s+(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\s+(?:now|today|currently|right\s+now|at\s+the\s+moment|this\s+moment))?(?:\s*[\?\.])?$",
            ]
            
            location = "current location"
            for pattern in location_patterns:
                match = re.search(pattern, user_input)
                if match:
                    location = match.group(1).strip()
                    # Remove common time-related words that might have been captured
                    time_words = ['now', 'today', 'currently', 'right now', 'at the moment', 'this moment']
                    for time_word in time_words:
                        # Remove time words from the end or anywhere in the location string
                        location = re.sub(f'\\s*{re.escape(time_word)}\\s*', ' ', location, flags=re.IGNORECASE)
                    # Clean up multiple spaces and strip
                    location = re.sub(r'\s+', ' ', location).strip()
                    break
            
            # Get real weather data from OpenWeatherMap API
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
                    "weather_source": "openweathermap_api"
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
        Get real weather data for a location using OpenWeatherMap API
        """
        import httpx
        from core.config import settings
        
        if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY == "your_openweather_api_key_here":
            raise ValueError("OpenWeatherMap API key is not configured. Please set OPENWEATHER_API_KEY in your .env file.")
        
        logger.info(f"Fetching weather data for location: {location}")
        
        # OpenWeatherMap API call
        url = settings.OPENWEATHER_API_URL
        params = {
            "q": location,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric"  # Use Celsius
        }
        
        # Configure httpx client with SSL verification disabled for corporate environments
        # and additional timeout settings
        try:
            async with httpx.AsyncClient(
                timeout=30.0, 
                verify=False,
                follow_redirects=True
            ) as client:
                logger.debug(f"Making API request to: {url} with params: {params}")
                response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract weather information
                temp = data["main"]["temp"]
                temp_f = (temp * 9/5) + 32
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                pressure = data["main"]["pressure"]
                condition = data["weather"][0]["description"].title()
                wind_speed = data["wind"].get("speed", 0) * 3.6  # Convert m/s to km/h
                country = data["sys"]["country"]
                city_name = data["name"]
                
                weather_report = f"""🌤️ Real-Time Weather Report:
    
📍 Location: {city_name}, {country}
🌡️ Temperature: {temp:.1f}°C ({temp_f:.1f}°F)
🤗 Feels like: {feels_like:.1f}°C
☁️ Condition: {condition}
💧 Humidity: {humidity}%
🏔️ Pressure: {pressure} hPa
💨 Wind Speed: {wind_speed:.1f} km/h

🔗 Powered by OpenWeatherMap API"""
                
                return weather_report
            
            elif response.status_code == 404:
                raise ValueError(f"Location '{location}' not found. Please check the spelling and try again.")
            
            elif response.status_code == 401:
                raise ValueError("OpenWeatherMap API key is invalid or unauthorized. Please check your API key.")
            
            else:
                raise Exception(f"Weather API returned status {response.status_code}: {response.text}")
                
        except httpx.TimeoutException:
            raise Exception("Weather API request timed out. Please try again.")
        except httpx.ConnectError as e:
            raise Exception(f"Cannot connect to weather API: {str(e)}")
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            raise Exception(f"Weather service error: {str(e)}")



class ChatConversationTool(BaseTool):
    """Tool for general conversation using Mistral AI - used as fallback when documents don't have answers"""
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.CHAT_CONVERSATION
    
    @property
    def description(self) -> str:
        return "General conversation and knowledge - fallback when documents don't contain the answer"
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute general conversation with creative responses"""
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
            
            # Create a creative conversational prompt
            conversation_prompt = f"""You are a helpful and creative AI assistant. The user asked a question that wasn't found in the available documents, so now you're helping with general knowledge and conversation.

🤖 Context: The user's question couldn't be answered from the uploaded documents, so you're providing general assistance.

User message: {request.user_input}

Respond in a friendly, helpful, and engaging way. Be creative and informative. If it's a greeting, be warm. If it's a question, provide helpful general knowledge. Always acknowledge that this information comes from your general knowledge rather than specific documents.

Start your response with a friendly acknowledgment like:
- "I don't have that specific information in the uploaded documents, but I can help with some general knowledge!"
- "That's not in our document library, but here's what I know about that topic!"
- "I couldn't find that in the PDFs, but let me share some general insights!"

Response:"""

            response = await mistral_service.generate_response(
                user_message=conversation_prompt,
                user_id=request.user_id,
                conversation_history=request.context.get("conversation_history", []) if request.context else []
            )
            
            execution_time = time.time() - start_time
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result=response,
                message="General conversation - information from AI knowledge base",
                metadata={
                    "model": "mistral-ai",
                    "conversation_type": "fallback_general",
                    "source": "ai_general_knowledge"
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
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute document analysis"""
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
            
            # Create a document analysis prompt
            analysis_prompt = f"""You are a document analyst. Analyze the available documents and provide comprehensive insights based on the user's request.

User request: {request.user_input}

Instructions:
1. Examine the content, structure, and key themes in the documents
2. Identify main topics, patterns, and important information
3. Provide insights about document organization and content
4. Highlight key findings, conclusions, or recommendations
5. Analyze the document types, quality, and completeness

Please provide a detailed analysis:"""
            
            response = await rag_service.query_documents(
                query=analysis_prompt,
                user_id=request.user_id,
                session_id="analysis_session"
            )
            
            execution_time = time.time() - start_time
            
            # Extract the answer from the RAG response
            result = response.get("answer", "No documents found to analyze")
            
            return ToolResponse(
                success=True,
                tool_used=self.tool_type,
                result=result,
                message="Document analysis completed successfully",
                metadata={
                    "analysis_type": "content_analysis",
                    "context_used": response.get("context_used", 0),
                    "source_chunks": len(response.get("source_chunks", []))
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
            summary_prompt = f"""You are tasked with creating a summary. Based on the user's request, search through available documents and provide a clear, concise summary.

User request: {request.user_input}

Instructions:
1. Search for relevant information in the documents
2. Extract key points, main ideas, and important details
3. Organize the information logically
4. Present a clear and comprehensive summary
5. Include specific details and examples where relevant

Provide a well-structured summary:"""
            
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
            ChatConversationTool()  # Fallback for when documents don't have answers
        ]
        self.logger = logging.getLogger("tool_orchestrator")
    
    async def analyze_intent_with_llm(self, request: ToolRequest) -> Dict[ToolType, float]:
        """
        Use LLM to intelligently analyze user intent and classify the request
        """
        try:
            if mistral_service is None:
                self.logger.warning("Mistral service not available, falling back to keyword-based analysis")
                return await self.analyze_intent_fallback(request)
            
            # Create classification prompt
            classification_prompt = f"""You are an intelligent request classifier. Analyze the user's message and determine what type of action they want to perform.

Available tool types:
1. SEMANTIC_SEARCH - Search through uploaded documents, PDFs, files for specific information
2. WEATHER - Get weather information for locations  
3. DOCUMENT_UPLOAD - Upload or process new documents
4. SUMMARIZATION - Summarize content, create brief overviews, key points
5. FILE_ANALYSIS - Analyze document structure, content insights, document breakdown
6. DATABASE_QUERY - Query database information
7. EMBEDDING_GENERATION - Generate embeddings for text
8. TRANSLATION - Translate text between languages
9. CODE_GENERATION - Generate or help with code

User message: "{request.user_input}"

CRITICAL CLASSIFICATION RULES:
- Questions about procedures, processes, policies, tickets, systems, tools, or specific business operations -> SEMANTIC_SEARCH
- Questions starting with "how to", "what is", "where can I", "when should", "why does" about business topics -> SEMANTIC_SEARCH
- Questions about company-specific terms, acronyms, or technical procedures -> SEMANTIC_SEARCH
- Questions about software tools, applications, platforms, or technical processes -> SEMANTIC_SEARCH
- Weather queries with location names -> WEATHER
- All other questions -> SEMANTIC_SEARCH
- Requests to summarize existing content -> SUMMARIZATION

Examples for SEMANTIC_SEARCH:
- "how to open a EUP ticket?"
- "how to open a ticket for dataiku?"
- "what is the process for..."
- "how do I access..."
- "where can I find information about..."
- "what are the requirements for..."

Respond with ONLY the tool type name (e.g., "SEMANTIC_SEARCH") that best matches the user's intent.

Tool type:"""

            # Get classification from LLM
            response = await mistral_service.generate_response(
                user_message=classification_prompt,
                user_id=request.user_id,
                conversation_history=[]
            )
            
            # Parse the LLM response
            predicted_tool = response.strip().upper()
            self.logger.info(f"LLM classified intent as: {predicted_tool}")
            
            # Convert to confidence scores
            tool_scores = {}
            for tool_type in ToolType:
                if tool_type.name == predicted_tool:
                    tool_scores[tool_type] = 0.95  # High confidence for LLM prediction
                else:
                    tool_scores[tool_type] = 0.05  # Low confidence for others
            
            # If LLM prediction doesn't match any tool, fall back to keyword analysis
            if not any(score > 0.9 for score in tool_scores.values()):
                self.logger.warning(f"LLM prediction '{predicted_tool}' not recognized, using fallback")
                return await self.analyze_intent_fallback(request)
            
            return tool_scores
            
        except Exception as e:
            self.logger.error(f"LLM intent analysis failed: {str(e)}, falling back to keyword analysis")
            return await self.analyze_intent_fallback(request)
    
    async def analyze_intent_fallback(self, request: ToolRequest) -> Dict[ToolType, float]:
        """
        Simple fallback when LLM is not available - defaults to semantic search
        """
        self.logger.warning("Using fallback intent analysis - defaulting to semantic search")
        
        tool_scores = {}
        # Initialize all tools with low confidence
        for tool in self.tools:
            tool_scores[tool.tool_type] = 0.1
        
        # Check if it's likely a weather query
        query_lower = request.user_input.lower()
        weather_indicators = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy"]
        
        if any(indicator in query_lower for indicator in weather_indicators):
            tool_scores[ToolType.WEATHER] = 0.8
        else:
            # Default to semantic search when LLM is not available (chat will be fallback)
            tool_scores[ToolType.SEMANTIC_SEARCH] = 0.8
            tool_scores[ToolType.CHAT_CONVERSATION] = 0.2  # Available as fallback
        
        return tool_scores
    
    async def analyze_intent(self, request: ToolRequest) -> Dict[ToolType, float]:
        """
        Main intent analysis method - uses LLM first, falls back to keywords
        """
        return await self.analyze_intent_with_llm(request)
    
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
        Main execution method - analyzes intent and routes to appropriate tool with intelligent fallback
        """
        try:
            self.logger.info(f"Processing request: {request.user_input[:100]}...")
            
            # Check if it's a weather query first
            query_lower = request.user_input.lower()
            weather_indicators = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy"]
            is_weather_query = any(indicator in query_lower for indicator in weather_indicators)
            
            if is_weather_query:
                # Handle weather queries
                weather_tool = WeatherTool()
                response = await weather_tool.execute(request)
                self.logger.info(f"Weather tool execution completed. Success: {response.success}")
                return response
            else:
                # For all non-weather queries, try semantic search first
                self.logger.info("Non-weather query detected, trying semantic search first")
                semantic_tool = SemanticSearchTool()
                semantic_response = await semantic_tool.execute(request)
                
                if semantic_response.success and semantic_response.result:
                    # Check if we got meaningful content
                    result_text = str(semantic_response.result).lower()
                    
                    # Check for "no content" indicators
                    no_content_indicators = [
                        "no answer found", "no relevant information", "i don't have information",
                        "no documents found", "cannot find", "not available in the documents",
                        "no content available", "i cannot provide information", "i don't know",
                        "not mentioned in", "no information about", "no specific information"
                    ]
                    
                    has_no_content = any(indicator in result_text for indicator in no_content_indicators)
                    is_too_short = len(result_text.strip()) < 20
                    
                    if has_no_content or is_too_short:
                        # No meaningful content found in documents - fall back to conversation
                        self.logger.info("No relevant content in documents, falling back to general conversation")
                        chat_tool = ChatConversationTool()
                        chat_response = await chat_tool.execute(request)
                        
                        if chat_response.success:
                            # Add metadata to indicate this was a fallback
                            chat_response.metadata = chat_response.metadata or {}
                            chat_response.metadata["fallback_reason"] = "no_document_content"
                            chat_response.metadata["tried_semantic_search"] = True
                            return chat_response
                        else:
                            # If chat also fails, return a helpful message
                            return ToolResponse(
                                success=True,
                                tool_used=ToolType.CHAT_CONVERSATION,
                                result="I don't have information about that topic in my documents, and I'm having trouble accessing my general knowledge right now. Please try rephrasing your question or upload relevant documents.",
                                message="Both document search and general conversation failed",
                                metadata={"fallback_failed": True}
                            )
                    else:
                        # Found meaningful content in documents
                        self.logger.info("Found relevant content in documents")
                        semantic_response.message = "Found relevant information in knowledge base"
                        semantic_response.metadata = semantic_response.metadata or {}
                        semantic_response.metadata["source"] = "document_knowledge"
                        return semantic_response
                else:
                    # Semantic search failed - fall back to conversation
                    self.logger.info("Semantic search failed, falling back to general conversation")
                    chat_tool = ChatConversationTool()
                    chat_response = await chat_tool.execute(request)
                    
                    if chat_response.success:
                        chat_response.metadata = chat_response.metadata or {}
                        chat_response.metadata["fallback_reason"] = "semantic_search_failed"
                        return chat_response
                    else:
                        # Both failed
                        return ToolResponse(
                            success=False,
                            tool_used=ToolType.CHAT_CONVERSATION,
                            result="I'm having trouble accessing both my document library and general knowledge. Please try again later.",
                            message="Both semantic search and conversation failed",
                            metadata={"total_failure": True}
                        )
            
        except Exception as e:
            self.logger.error(f"Orchestrator execution failed: {str(e)}")
            return ToolResponse(
                success=False,
                tool_used=ToolType.CHAT_CONVERSATION,
                result="Sorry, I encountered an unexpected error. Please try again later.",
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