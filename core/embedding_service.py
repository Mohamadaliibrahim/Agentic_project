"""
Embedding Service
Generates embeddings for text chunks and handles similarity search
"""

import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self):
        # For now, we'll use a simple method, but this can be extended
        # to use OpenAI embeddings, sentence-transformers, or other services
        self.embedding_dimension = 384  # Common dimension for sentence-transformers
        self.use_local_embeddings = True  # Set to False to use external API
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.use_local_embeddings:
                return await self._generate_simple_embeddings(texts)
            else:
                # Future: implement external embedding API calls
                return await self._generate_api_embeddings(texts)
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    async def _generate_simple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate simple embeddings using text characteristics
        This is a basic implementation - in production, use proper embedding models
        """
        embeddings = []
        
        for text in texts:
            words = text.lower().split()
            chars = list(text.lower())
            
            features = [
                len(text),
                len(words),
                len(set(words)),
                len(set(chars)),
                text.count('.'),
                text.count(','),
                text.count('?'),
                text.count('!'),
            ]
            
            common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'under', 'between']
            for word in common_words:
                features.append(text.lower().count(word))
            
            # Pad or truncate to desired dimension
            while len(features) < self.embedding_dimension:
                features.append(0.0)
            
            features = features[:self.embedding_dimension]

            norm = np.linalg.norm(features)
            if norm > 0:
                features = [f / norm for f in features]
            
            embeddings.append(features)
        
        return embeddings
    
    async def _generate_api_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using external API (future implementation)
        This could use OpenAI, Hugging Face, or other embedding services
        """
        # Placeholder for external API implementation
        # For example, using OpenAI embeddings API:
        
        # headers = {
        #     "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        #     "Content-Type": "application/json"
        # }
        # 
        # payload = {
        #     "input": texts,
        #     "model": "text-embedding-ada-002"
        # }
        # 
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.openai.com/v1/embeddings",
        #         headers=headers,
        #         json=payload
        #     )
        #     
        #     if response.status_code == 200:
        #         result = response.json()
        #         return [item["embedding"] for item in result["data"]]
        
        # For now, fall back to simple embeddings
        return await self._generate_simple_embeddings(texts)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the most similar embeddings to a query embedding
        
        Args:
            query_embedding: The query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with indices and similarity scores
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    "index": i,
                    "similarity": similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {str(e)}")
            return []

# Create singleton instance
embedding_service = EmbeddingService()
