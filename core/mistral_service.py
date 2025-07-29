import httpx
import json
from core.config import settings

class MistralAIService:
    """Service for interacting with Mistral AI API"""
    
    def __init__(self):
        self.api_endpoint = settings.MISTRAL_API_ENDPOINT
        self.api_key = settings.MISTRAL_API_KEY
        self.model = settings.MISTRAL_MODEL
        
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
                "content": "You are a helpful AI assistant. Provide concise, helpful, and friendly responses to user questions. Use the conversation history to provide contextually relevant responses. Answers should be short and not exceed 10 words."
            }
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": "user",
                    "content": msg.get("user_msg", "")
                })
                messages.append({
                    "role": "assistant", 
                    "content": msg.get("assistant_msg", "")
                })
        
        # Add current user message
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
