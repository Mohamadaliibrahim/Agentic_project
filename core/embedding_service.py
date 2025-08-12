"""
Embedding Service
Generates embeddings for text chunks using Mistral AI API and handles similarity search
"""

import logging
import numpy as np
import httpx
import json
from typing import List, Dict, Any
from core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing text embeddings using Mistral AI"""
    
    def __init__(self):
        self.api_endpoint = settings.MISTRAL_API_EMBEDDING
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_EMBEDDING_MODEL
        self.embedding_dimension = 1024  # Mistral codestral-embed dimension
        self.use_mistral_api = True if self.api_key else False
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Mistral API
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.use_mistral_api and self.api_key:
                return await self._generate_mistral_embeddings(texts)
            else:
                logger.warning("Mistral API not configured, falling back to simple embeddings")
                return await self._generate_simple_embeddings(texts)
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Fallback to simple embeddings if API fails
            logger.warning("Falling back to simple embeddings due to API error")
            return await self._generate_simple_embeddings(texts)
    
    async def _generate_mistral_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Mistral AI API
        """
        if not self.api_key:
            raise Exception("Mistral API key not configured")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Mistral API accepts batch requests, but let's process in smaller batches
        batch_size = 10  # Process 10 texts at a time
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            payload = {
                "model": self.model,
                "input": batch_texts
            }
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.api_endpoint,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if "data" in result:
                            batch_embeddings = [item["embedding"] for item in result["data"]]
                            all_embeddings.extend(batch_embeddings)
                        else:
                            logger.error(f"Unexpected response format from Mistral API: {result}")
                            raise Exception("Invalid response format from Mistral API")
                            
                    elif response.status_code == 401:
                        raise Exception("Mistral API authentication failed")
                    elif response.status_code == 429:
                        raise Exception("Mistral API rate limit exceeded")
                    else:
                        error_text = response.text if hasattr(response, 'text') else str(response.status_code)
                        raise Exception(f"Mistral API error {response.status_code}: {error_text}")
                        
            except httpx.TimeoutException:
                raise Exception("Mistral embedding API request timed out")
            except httpx.RequestError as e:
                raise Exception(f"Mistral embedding API request failed: {str(e)}")
            except json.JSONDecodeError:
                raise Exception("Mistral embedding API returned invalid JSON")
        
        logger.info(f"Generated {len(all_embeddings)} embeddings using Mistral API")
        return all_embeddings
    
    async def _generate_simple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate simple embeddings using text characteristics
        This is a fallback implementation when Mistral API is not available
        """
        embeddings = []
        
        # Use smaller dimension for simple embeddings (384) but pad to match Mistral
        simple_dimension = 384
        
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
            
            # Pad or truncate to simple dimension first
            while len(features) < simple_dimension:
                features.append(0.0)
            
            features = features[:simple_dimension]

            # Normalize the features
            norm = np.linalg.norm(features)
            if norm > 0:
                features = [f / norm for f in features]
            
            # Pad to match Mistral dimension (1024) for compatibility
            while len(features) < self.embedding_dimension:
                features.append(0.0)
            
            embeddings.append(features)
        
        logger.warning(f"Generated {len(embeddings)} simple embeddings (fallback mode)")
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
