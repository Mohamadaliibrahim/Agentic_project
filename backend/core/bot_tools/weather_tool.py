"""
Weather Tool
Retrieves weather information for a given location
"""

import httpx
import re
from typing import Dict, Any
from .base_tool import BaseBotTool, ToolResponse

class WeatherTool(BaseBotTool):
    """Tool for getting weather information"""
    
    @property
    def tool_name(self) -> str:
        return "weather_query"
    
    @property
    def description(self) -> str:
        return "Gets current weather information for any location worldwide"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city, country, or location to get weather for (e.g., 'New York', 'Paris, France', 'Tokyo')"
                }
            },
            "required": ["location"]
        }
    
    @property
    def llm_prompt_template(self) -> str:
        return """The user asked about weather: "{user_query}"

I retrieved the following weather data for {metadata[location]}:

Raw Weather Data:
{tool_data}

Please format this weather information in a friendly, easy-to-read way for the user. Include:
- Current temperature (both Celsius and Fahrenheit)
- Weather conditions
- How it feels like
- Humidity and wind information
- Any other relevant details

Make the response conversational and helpful. Use appropriate weather emojis to make it more engaging."""
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Execute weather query"""
        try:
            location = parameters.get("location", "").strip()
            if not location:
                return ToolResponse(
                    success=False,
                    error="Location parameter is required"
                )
            
            # Get weather data from API
            weather_data = await self._fetch_weather_data(location)
            
            return ToolResponse(
                success=True,
                data=weather_data,
                metadata={"location": location, "source": "openweathermap"}
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"Weather query failed: {str(e)}"
            )
    
    async def _fetch_weather_data(self, location: str) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap API"""
        from core.config import settings
        
        if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY == "your_openweather_api_key_here":
            raise ValueError("OpenWeatherMap API key is not configured")
        
        url = settings.OPENWEATHER_API_URL
        params = {
            "q": location,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric"  # Celsius
        }
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Structure the weather data
                return {
                    "location": {
                        "name": data["name"],
                        "country": data["sys"]["country"]
                    },
                    "temperature": {
                        "celsius": round(data["main"]["temp"], 1),
                        "fahrenheit": round((data["main"]["temp"] * 9/5) + 32, 1),
                        "feels_like_celsius": round(data["main"]["feels_like"], 1)
                    },
                    "weather": {
                        "condition": data["weather"][0]["description"].title(),
                        "main": data["weather"][0]["main"]
                    },
                    "details": {
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "wind_speed_kmh": round(data["wind"].get("speed", 0) * 3.6, 1)
                    },
                    "timestamp": data.get("dt")
                }
            
            elif response.status_code == 404:
                raise ValueError(f"Location '{location}' not found")
            elif response.status_code == 401:
                raise ValueError("Weather API key is invalid")
            else:
                raise Exception(f"Weather API error: {response.status_code}")
                
    def extract_location_from_query(self, user_query: str) -> str:
        """Extract location from natural language query"""
        query_lower = user_query.lower()
        
        # Location extraction patterns
        location_patterns = [
            r"weather (?:in|at|for) ([a-zA-Z\s,]+?)(?:\s+(?:now|today|currently))?(?:\s*[\?\.])?$",
            r"temperature (?:in|at|for) ([a-zA-Z\s,]+?)(?:\s+(?:now|today|currently))?(?:\s*[\?\.])?$",
            r"(?:in|at|for) ([a-zA-Z\s,]+?)(?:\s+(?:now|today|currently))?\s+weather",
            r"what(?:'s|\s+is)\s+the\s+weather\s+(?:in|at|for)\s+([a-zA-Z\s,]+?)(?:\s+(?:now|today|currently))?(?:\s*[\?\.])?$",
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                # Clean up time-related words
                time_words = ['now', 'today', 'currently', 'right now']
                for time_word in time_words:
                    location = re.sub(f'\\s*{re.escape(time_word)}\\s*', ' ', location, flags=re.IGNORECASE)
                return re.sub(r'\s+', ' ', location).strip()
        
        return "current location"