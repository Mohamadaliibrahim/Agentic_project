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
        self.embedding_dimension = 1024
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
                raise Exception("Mistral API not configured and no fallback available")
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
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
        
        # Use smaller batches for large document sets to avoid timeouts
        batch_size = settings.MISTRAL_EMBEDDING_BATCH_SIZE_SMALL if len(texts) > settings.MISTRAL_EMBEDDING_BATCH_THRESHOLD else settings.MISTRAL_EMBEDDING_BATCH_SIZE_LARGE
        all_embeddings = []
        
        logger.info(f"Processing {len(texts)} text chunks in batches of {batch_size}")
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} chunks)")
            
            payload = {
                "model": self.model,
                "input": batch_texts
            }
            
            # Retry logic for failed requests
            for attempt in range(settings.MISTRAL_MAX_RETRIES):
                try:
                    # Longer timeout for large documents
                    async with httpx.AsyncClient(timeout=settings.MISTRAL_EMBEDDING_TIMEOUT) as client:
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
                        if attempt < settings.MISTRAL_MAX_RETRIES - 1:
                            logger.warning(f"Batch {batch_num} failed (attempt {attempt + 1}), retrying...")
                            continue
                        else:
                            raise Exception(f"Mistral API error {response.status_code}: {error_text}")
                            
                    # If we get here, the request was successful
                    break
                        
                except httpx.TimeoutException:
                    if attempt < settings.MISTRAL_MAX_RETRIES - 1:
                        logger.warning(f"Batch {batch_num} timed out (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        raise Exception(f"Mistral embedding API request timed out after {settings.MISTRAL_MAX_RETRIES} attempts")
                except httpx.RequestError as e:
                    if attempt < settings.MISTRAL_MAX_RETRIES - 1:
                        logger.warning(f"Batch {batch_num} request failed (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        raise Exception(f"Mistral embedding API request failed: {str(e)}")
                except json.JSONDecodeError:
                    if attempt < settings.MISTRAL_MAX_RETRIES - 1:
                        logger.warning(f"Batch {batch_num} returned invalid JSON (attempt {attempt + 1}), retrying...")
                        continue
                    else:
                        raise Exception("Mistral embedding API returned invalid JSON")
        
        logger.info(f"Generated {len(all_embeddings)} embeddings using Mistral API")
        return all_embeddings
embedding_service = EmbeddingService()
