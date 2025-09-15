import httpx
import json
import logging
from core.config import settings
from datetime import datetime
from core.logger import log_debug_session, log_info_session, log_timing, log_error_session, log_prompt

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
        
    async def generate_response(self, user_message: str, user_id: str = None, conversation_history: list = None, session_id: str = None) -> str:
        if not session_id:
            session_id = "unknown"
            
        if not self.api_key:
            log_error_session(session_id, "API key not configured")
            return "AI service is not configured. Please contact the administrator."
        
        log_info_session(session_id, "mistral_service.py", "Starting response generation...")
        log_debug_session(session_id, "mistral_service.py", f"User ID={user_id}")
        log_debug_session(session_id, "mistral_service.py", f"Message length={len(user_message)} chars")
        log_debug_session(session_id, "mistral_service.py", f"Model={self.model}")
        
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
            log_debug_session(session_id, "mistral_service.py", f"Processing {len(conversation_history)} conversation history messages")
            limited_history = self.limit_conversation_history(conversation_history)
            log_debug_session(session_id, "mistral_service.py", f"Using {len(limited_history)} messages after token limiting")
            
            for i, msg in enumerate(limited_history, 1):
                messages.append({
                    "role": "user",
                    "content": msg.get("user_message", "")
                })
                messages.append({
                    "role": "assistant", 
                    "content": msg.get("assistant_message", "")
                })
                log_debug_session(session_id, "mistral_service.py", f"History {i}: User='{msg.get('user_message', '')[:30]}...' | AI='{msg.get('assistant_message', '')[:30]}...'")
        else:
            log_debug_session(session_id, "mistral_service.py", "No conversation history provided")

        messages.append({
            "role": "user",
            "content": user_message
        })
        
        log_debug_session(session_id, "mistral_service.py", f"Total messages in context: {len(messages)}")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        # Log the complete prompt for debugging
        full_prompt = json.dumps(messages, indent=2)
        # We'll log the prompt after we get the response in the try block
        
        log_debug_session(session_id, "mistral_service.py", f"Payload prepared - max_tokens={payload['max_tokens']}, temperature={payload['temperature']}")
        log_info_session(session_id, "mistral_service.py", "Using 60-second timeout for API requests")
        
        try:
            api_start = datetime.utcnow()
            log_debug_session(session_id, "mistral_service.py", "Sending request to Mistral AI API...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout to 60 seconds
                response = await client.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload
                )
                
                api_end = datetime.utcnow()
                api_duration = (api_end - api_start).total_seconds()
                
                log_timing(session_id, "mistral_api_call", api_duration, f"HTTP {response.status_code}")
                log_debug_session(session_id, "mistral_service.py", f"API response received in {api_duration:.3f}s")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Log API usage statistics if available
                    if "usage" in result:
                        usage = result["usage"]
                        log_debug_session(session_id, "mistral_service.py", f"Token usage - prompt: {usage.get('prompt_tokens', 'N/A')}, completion: {usage.get('completion_tokens', 'N/A')}, total: {usage.get('total_tokens', 'N/A')}")
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        ai_response = result["choices"][0]["message"]["content"].strip()
                        
                        # Log the complete prompt and response for audit
                        log_prompt(session_id, full_prompt, ai_response, "mistral_request")
                        
                        log_info_session(session_id, "mistral_service.py", f"Response generated successfully")
                        log_debug_session(session_id, "mistral_service.py", f"Response length: {len(ai_response)} characters")
                        log_debug_session(session_id, "mistral_service.py", f"Response preview: '{ai_response[:100]}...'")
                        return ai_response
                    else:
                        log_error_session(session_id, "No choices in API response")
                        log_debug_session(session_id, "mistral_service.py", f"Response structure: {result}")
                        return "I apologize, but I couldn't generate a proper response. Please try again."
                        
                elif response.status_code == 401:
                    log_error_session(session_id, "Authentication failed (401)")
                    return "AI service authentication failed. Please contact the administrator."
                elif response.status_code == 429:
                    log_error_session(session_id, "Rate limit exceeded (429)")
                    return "AI service is currently busy. Please try again in a moment."
                elif response.status_code == 503:
                    log_error_session(session_id, "Service unavailable (503) - Mistral AI servers are temporarily down")
                    return "The AI service is currently experiencing high demand or maintenance. Please try again in a few minutes."
                else:
                    log_error_session(session_id, f"API error - Status code: {response.status_code}")
                    log_debug_session(session_id, "mistral_service.py", f"Error response: {response.text}")
                    return f"AI service temporarily unavailable (Error {response.status_code}). Please try again later."
                    
        except httpx.TimeoutException:
            log_error_session(session_id, "Request timed out (60 second timeout)")
            return "AI service request timed out after 60 seconds. The query may be too complex. Please try a simpler question."
        except httpx.RequestError as e:
            log_error_session(session_id, f"Request error: {str(e)}")
            return "AI service is currently unavailable. Please try again later."
        except json.JSONDecodeError:
            log_error_session(session_id, "Invalid JSON response from API")
            return "AI service returned an invalid response. Please try again."
        except Exception as e:
            log_error_session(session_id, f"Unexpected error: {str(e)}")
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
