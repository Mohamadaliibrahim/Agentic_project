"""
RAG (Retrieval-Augmented Generation) Service
Combines document retrieval with Mistral AI for context-aware responses
"""

import logging
from typing import List, Dict, Any
from core.mistral_service import mistral_service
from core.embedding_service import embedding_service
from database.factory import get_db
from datetime import datetime

logger = logging.getLogger("rag_service")

class RAGService:
    """Service for Retrieval-Augmented Generation using document chunks"""
    
    def __init__(self, max_context_chunks: int = 5, max_context_length: int = 2000):
        self.max_context_chunks = max_context_chunks
        self.max_context_length = max_context_length
    
    async def query_documents(
        self, 
        query: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Query documents using RAG approach with shared vector_storage (like rag_testing notebook)
        Searches across ALL user documents in shared .pkl file (no document_id needed)
        
        Args:
            query: User's question
            user_id: ID of the user making the query
            
        Returns:
            Dictionary with answer and source chunks
        """
        try:
            logger.info(f"RAG SERVICE: Starting document search for user {user_id}")
            logger.info(f"RAG SERVICE: Query='{query}'")
            logger.info(f"RAG SERVICE: Max chunks to retrieve={self.max_context_chunks}")
            search_start = datetime.utcnow()
            
            from core.document_processor import document_processor
            
            logger.info("RAG SERVICE: Calling document processor for search...")
            search_results = await document_processor.search_user_documents(
                user_id=user_id,
                query=query,
                top_k=self.max_context_chunks
            )
            
            search_end = datetime.utcnow()
            search_duration = (search_end - search_start).total_seconds()
            logger.info(f"RAG SERVICE: Document search completed in {search_duration:.3f}s")
            logger.info(f"RAG SERVICE: Found {len(search_results) if search_results else 0} results")
            
            if not search_results:
                logger.warning("RAG SERVICE: No search results found - returning default response")
                return {
                    "answer": "I couldn't find any relevant information in your documents to answer this question.",
                    "source_chunks": [],
                    "query": query,
                    "context_used": 0
                }
            
            logger.info("RAG SERVICE: Processing search results...")
            relevant_chunks = []
            for i, result in enumerate(search_results[:self.max_context_chunks], 1):  # Ensure we only take top max_context_chunks
                metadata = result["metadata"]
                score = result["score"]
                logger.debug(f"   Result {i}: {metadata['filename']} (score: {score:.3f})")
                
                chunk_data = {
                    "text": metadata["content"],
                    "document_id": metadata["document_id"],
                    "chunk_id": metadata.get("chunk_id", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "filename": metadata["filename"],
                    "similarity_score": score,
                    "published_date": metadata["published_date"]
                }
                relevant_chunks.append(chunk_data)
            
            # Explicit check to ensure we don't exceed 5 chunks
            if len(relevant_chunks) > 5:
                logger.warning(f"RAG SERVICE: Limiting {len(relevant_chunks)} chunks to top 5 most similar")
                relevant_chunks = relevant_chunks[:5]
            
            logger.info(f"RAG SERVICE: Using {len(relevant_chunks)} chunks (max allowed: {self.max_context_chunks})")
            
            # Log details of selected chunks
            for i, chunk in enumerate(relevant_chunks, 1):
                logger.info(f"   Chunk {i}: {chunk['filename']} | Score: {chunk['similarity_score']:.4f} | Length: {len(chunk['text'])} chars")
            
            logger.info(f"RAG SERVICE: Processed {len(relevant_chunks)} chunks")
            
            logger.info("RAG SERVICE: Preparing context from chunks...")
            context_start = datetime.utcnow()
            context = self._prepare_context(relevant_chunks)
            context_end = datetime.utcnow()
            context_duration = (context_end - context_start).total_seconds()
            
            logger.info(f"RAG SERVICE: Context prepared in {context_duration:.3f}s")
            logger.info(f"RAG SERVICE: Context length: {len(context)} characters")
            
            logger.info("RAG SERVICE: Generating AI response from context...")
            response_start = datetime.utcnow()
            answer = await self._generate_rag_response(query, context)
            response_end = datetime.utcnow()
            response_duration = (response_end - response_start).total_seconds()
            
            logger.info(f"RAG SERVICE: AI response generated in {response_duration:.3f}s")
            logger.info(f"RAG SERVICE: Response length: {len(answer)} characters")
            
            response = {
                "answer": answer,
                "source_chunks": self._format_source_chunks(relevant_chunks),
                "query": query,
                "context_used": len(relevant_chunks)
            }
            
            total_time = (response_end - search_start).total_seconds()
            logger.info(f"RAG SERVICE: Query completed successfully in {total_time:.3f}s total")
            logger.info(f"RAG SERVICE: Used {len(relevant_chunks)} chunks from shared storage")
            return response
            
        except Exception as e:
            logger.error(f"RAG SERVICE ERROR: {str(e)}")
            logger.error(f"RAG SERVICE: Query='{query}', User={user_id}")
            logger.error("RAG SERVICE: Full error details:", exc_info=True)
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "source_chunks": [],
                "query": query,
                "context_used": 0
            }
    
    def _prepare_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context string from relevant chunks"""
        context_parts = []
        total_length = 0
        
        for chunk in chunks:
            chunk_text = chunk["text"]
            
            if total_length + len(chunk_text) > self.max_context_length:
                remaining_space = self.max_context_length - total_length
                if remaining_space > 100:
                    chunk_text = chunk_text[:remaining_space] + "..."
                    context_parts.append(f"[Document: {chunk['filename']}]\n{chunk_text}")
                break
            
            context_parts.append(f"[Document: {chunk['filename']}]\n{chunk_text}")
            total_length += len(chunk_text)
        
        return "\n\n".join(context_parts)
    
    async def _generate_rag_response(self, query: str, context: str) -> str:
        """Generate response using Mistral AI with document context"""
        try:
            rag_prompt = f"""You are a helpful AI assistant that answers questions based on provided document content.

            Context from documents:
            {context}

            User Question: {query}

            Instructions:
            - Answer the question using ONLY the information provided in the context above
            - If the context doesn't contain enough information to answer the question, say so clearly
            - Be specific and cite relevant parts of the documents when possible
            - If you're unsure about something, express that uncertainty
            - Keep your response concise but informative

            Answer:"""
            
            response = await mistral_service.generate_response(
                user_message=rag_prompt,
                user_id="rag_system"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return f"I apologize, but I encountered an error while generating the response: {str(e)}"
    
    def _format_source_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source chunks for response"""
        formatted_chunks = []
        
        for chunk in chunks:
            formatted_chunk = {
                "document_id": chunk["document_id"],
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "similarity_score": round(chunk.get("similarity_score", 0), 3)
            }
            formatted_chunks.append(formatted_chunk)
        
        return formatted_chunks

rag_service = RAGService()
