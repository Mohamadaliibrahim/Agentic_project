import httpx
import json
import logging
from core.config import settings

logger = logging.getLogger(__name__)

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
            return "AI service is not configured. Please contact the administrator."
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Build messages with conversation history
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Provide concise, helpful, and friendly responses to user questions. Use the conversation history to provide contextually relevant responses."
            }
        ]
        
        # Add conversation history if available (limited to token budget)
        if conversation_history:
            # Limit conversation history to fit within token budget
            limited_history = self.limit_conversation_history(conversation_history)
            
            # Add the limited history to messages
            for msg in limited_history:
                messages.append({
                    "role": "user",
                    "content": msg.get("user_message", "")
                })
                messages.append({
                    "role": "assistant", 
                    "content": msg.get("assistant_message", "")
                })

        messages.append({
            "role": "user",
            "content": user_message
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
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
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        ai_response = result["choices"][0]["message"]["content"].strip()
                        return ai_response
                    else:
                        return "I apologize, but I couldn't generate a proper response. Please try again."
                        
                elif response.status_code == 401:
                    return "AI service authentication failed. Please contact the administrator."
                elif response.status_code == 429:
                    return "AI service is currently busy. Please try again in a moment."
                else:
                    return f"AI service temporarily unavailable (Error {response.status_code}). Please try again later."
                    
        except httpx.TimeoutException:
            return "AI service request timed out. Please try again."
        except httpx.RequestError as e:
            return "AI service is currently unavailable. Please try again later."
        except json.JSONDecodeError:
            return "AI service returned an invalid response. Please try again."
        except Exception as e:
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
