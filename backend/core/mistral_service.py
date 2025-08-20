import httpx
import json
import logging
from core.config import settings
from datetime import datetime

logger = logging.getLogger("mistral_service")

class MistralAIService:
    """Service for interacting with Mistral AI API"""
    
    def __init__(self):
        self.api_endpoint = settings.MISTRAL_API_ENDPOINT
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_MODEL
        self.max_context_tokens = 10
    
    def estimate_tokens(self, text: str) -> int:
        """
        Simple token estimation (roughly 4 characters per token for English)
        This is an approximation - actual tokenization may vary
        """
        return len(text) // 4
    
    def limit_conversation_history(self, conversation_history: list) -> list:
        """
        Limit conversation history to approximately max_context_tokens
        Keep the most recent messages that fit within the token limit
        """
        if not conversation_history:
            return []
        
        limited_history = []
        total_tokens = 0
        
        for msg in reversed(conversation_history):
            user_text = msg.get("user_message", "")
            assistant_text = msg.get("assistant_message", "")
            
            message_tokens = self.estimate_tokens(user_text) + self.estimate_tokens(assistant_text)
            
            if total_tokens + message_tokens > self.max_context_tokens:
                break
            
            limited_history.insert(0, msg)
            total_tokens += message_tokens
        
        if len(limited_history) < len(conversation_history):
            excluded_count = len(conversation_history) - len(limited_history)
            logger.info(f"Token limiting: Using {len(limited_history)} recent messages, excluded {excluded_count} older messages")
            logger.info(f"Context tokens used: ~{total_tokens}/{self.max_context_tokens}")
        
        return limited_history
        
    async def generate_response(self, user_message: str, user_id: str = None, conversation_history: list = None) -> str:
        if not self.api_key:
            logger.error("MISTRAL SERVICE: API key not configured")
            return "AI service is not configured. Please contact the administrator."
        
        logger.info("MISTRAL SERVICE: Starting response generation...")
        logger.info(f"MISTRAL SERVICE: User ID={user_id}")
        logger.info(f"MISTRAL SERVICE: Message length={len(user_message)} chars")
        logger.info(f"MISTRAL SERVICE: Model={self.model}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Provide concise, helpful, and friendly responses to user questions. Use the conversation history to provide contextually relevant responses."
            }
        ]
        
        if conversation_history:
            logger.info(f"MISTRAL SERVICE: Processing {len(conversation_history)} conversation history messages")
            limited_history = self.limit_conversation_history(conversation_history)
            logger.info(f"MISTRAL SERVICE: Using {len(limited_history)} messages after token limiting")
            
            for i, msg in enumerate(limited_history, 1):
                messages.append({
                    "role": "user",
                    "content": msg.get("user_message", "")
                })
                messages.append({
                    "role": "assistant", 
                    "content": msg.get("assistant_message", "")
                })
                logger.debug(f"   History {i}: User='{msg.get('user_message', '')[:30]}...' | AI='{msg.get('assistant_message', '')[:30]}...'")
        else:
            logger.info("MISTRAL SERVICE: No conversation history provided")

        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info(f"MISTRAL SERVICE: Total messages in context: {len(messages)}")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        logger.info(f"MISTRAL SERVICE: Payload prepared - max_tokens={payload['max_tokens']}, temperature={payload['temperature']}")
        logger.info("MISTRAL SERVICE: Using 60-second timeout for API requests")
        
        try:
            api_start = datetime.utcnow()
            logger.info("MISTRAL SERVICE: Sending request to Mistral AI API...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout to 60 seconds
                response = await client.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload
                )
                
                api_end = datetime.utcnow()
                api_duration = (api_end - api_start).total_seconds()
                
                logger.info(f"MISTRAL SERVICE: API response received in {api_duration:.3f}s")
                logger.info(f"MISTRAL SERVICE: HTTP status code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log API usage statistics if available
                    if "usage" in result:
                        usage = result["usage"]
                        logger.info(f"MISTRAL SERVICE: Token usage - prompt: {usage.get('prompt_tokens', 'N/A')}, completion: {usage.get('completion_tokens', 'N/A')}, total: {usage.get('total_tokens', 'N/A')}")
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        ai_response = result["choices"][0]["message"]["content"].strip()
                        logger.info(f"MISTRAL SERVICE: Response generated successfully")
                        logger.info(f"MISTRAL SERVICE: Response length: {len(ai_response)} characters")
                        logger.debug(f"MISTRAL SERVICE: Response preview: '{ai_response[:100]}...'")
                        return ai_response
                    else:
                        logger.error("MISTRAL SERVICE: No choices in API response")
                        logger.error(f"MISTRAL SERVICE: Response structure: {result}")
                        return "I apologize, but I couldn't generate a proper response. Please try again."
                        
                elif response.status_code == 401:
                    logger.error("MISTRAL SERVICE: Authentication failed (401)")
                    return "AI service authentication failed. Please contact the administrator."
                elif response.status_code == 429:
                    logger.warning("MISTRAL SERVICE: Rate limit exceeded (429)")
                    return "AI service is currently busy. Please try again in a moment."
                else:
                    logger.error(f"MISTRAL SERVICE: API error - Status code: {response.status_code}")
                    logger.error(f"MISTRAL SERVICE: Error response: {response.text}")
                    return f"AI service temporarily unavailable (Error {response.status_code}). Please try again later."
                    
        except httpx.TimeoutException:
            logger.error("MISTRAL SERVICE: Request timed out (60 second timeout)")
            return "AI service request timed out after 60 seconds. The query may be too complex. Please try a simpler question."
        except httpx.RequestError as e:
            logger.error(f"MISTRAL SERVICE: Request error: {str(e)}")
            return "AI service is currently unavailable. Please try again later."
        except json.JSONDecodeError:
            logger.error("MISTRAL SERVICE: Invalid JSON response from API")
            return "AI service returned an invalid response. Please try again."
        except Exception as e:
            logger.error(f"MISTRAL SERVICE: Unexpected error: {str(e)}", exc_info=True)
            return "An unexpected error occurred while processing your request. Please try again."
    
    async def health_check(self) -> bool:
        """
        Check if Mistral AI service is available
        
        Returns:
            True if service is available, False otherwise
        """
        if not self.api_key:
            return False
            
        try:
            test_response = await self.generate_response("Hello")
            return not test_response.startswith("AI service")
        except:
            return False

mistral_service = MistralAIService()
