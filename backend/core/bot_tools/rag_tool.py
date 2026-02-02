"""
RAG (Retrieval-Augmented Generation) Tool
Searches through uploaded documents using semantic search
Uses the existing RAG services from core
"""

from typing import Dict, Any
from .base_tool import BaseBotTool, ToolResponse
from ..prompt_loader import prompt_loader
from .tool_definition.schema_loader import load_tool_parameters

# Import existing RAG services from parent module
try:
    from ..rag_service import rag_service
except ImportError:
    rag_service = None

class RAGTool(BaseBotTool):
    """Tool for searching through uploaded documents"""
    
    @property
    def tool_name(self) -> str:
        return "rag_search"
    
    @property
    def description(self) -> str:
        return "Searches through uploaded documents to find relevant information based on user queries"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        # Load parameters schema from the JSON tool-definition file.
        # This will raise an exception if the JSON file is missing or malformed.
        return load_tool_parameters("rag_tool.json")
    
    @property
    def llm_prompt_template(self) -> str:
        # Load prompt from prompts.txt file
        prompt = prompt_loader.get_prompt(
            "tool_rag_response",
            user_query="{user_query}",
            rag_data="{tool_data}"
        )
        return prompt if prompt else "Answer based on: {tool_data}"
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Execute RAG search"""
        try:
            query = parameters.get("query", "").strip()
            user_id = parameters.get("user_id", "").strip()
            
            if not query:
                return ToolResponse(
                    success=False,
                    error="Query parameter is required"
                )
                
            if not user_id:
                return ToolResponse(
                    success=False,
                    error="User ID parameter is required"
                )
            
            # Use the existing RAG service
            if rag_service is None:
                return ToolResponse(
                    success=False,
                    error="RAG service is not available"
                )
            
            # Perform the document search
            search_results = await rag_service.query_documents(
                query=query,
                user_id=user_id,
                session_id="rag_tool_session"
            )
            
            # Extract and structure the results
            answer = search_results.get("answer", "No relevant information found")
            source_chunks = search_results.get("source_chunks", [])
            context_used = search_results.get("context_used", 0)
            
            # Check if we got meaningful results
            if not answer or answer.lower() in ["no answer found", "no relevant information"]:
                return ToolResponse(
                    success=False,
                    error="No relevant information found in the uploaded documents"
                )
            
            return ToolResponse(
                success=True,
                data={
                    "answer": answer,
                    "sources": source_chunks,
                    "relevant_chunks": len(source_chunks)
                },
                metadata={
                    "chunks_found": len(source_chunks),
                    "documents_searched": len(set(chunk.get("source", "unknown") for chunk in source_chunks)),
                    "context_used": context_used,
                    "confidence": "high" if len(source_chunks) > 2 else "medium" if len(source_chunks) > 0 else "low"
                }
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"Document search failed: {str(e)}"
            )
    
    def has_relevant_content(self, answer: str) -> bool:
        """Check if the answer contains relevant content"""
        if not answer or len(answer.strip()) < 20:
            return False
            
        no_content_indicators = [
            "no answer found", "no relevant information", "i don't have information",
            "no documents found", "cannot find", "not available in the documents",
            "no content available", "i cannot provide information", "i don't know"
        ]
        
        answer_lower = answer.lower()
        return not any(indicator in answer_lower for indicator in no_content_indicators)