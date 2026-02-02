"""
Prompt Loader
Loads and manages LLM prompts from prompts.txt file
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PromptLoader:
    """Loads and manages prompts from prompts.txt file"""
    
    def __init__(self, prompts_file: str = None):
        """
        Initialize the prompt loader
        
        Args:
            prompts_file: Path to prompts.txt file. If None, uses default location.
        """
        if prompts_file is None:
            # Default to prompts.txt in the backend directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompts_file = os.path.join(os.path.dirname(current_dir), "prompts.txt")
        
        self.prompts_file = prompts_file
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompts from the prompts.txt file"""
        try:
            if not os.path.exists(self.prompts_file):
                logger.error(f"Prompts file not found: {self.prompts_file}")
                self._load_default_prompts()
                return
            
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the prompts file
            current_key = None
            current_prompt = []
            
            for line in content.split('\n'):
                # Check if this is a section header [key]
                if line.strip().startswith('[') and line.strip().endswith(']'):
                    # Save previous prompt if exists
                    if current_key:
                        self.prompts[current_key] = '\n'.join(current_prompt).strip()
                    
                    # Start new prompt
                    current_key = line.strip()[1:-1]  # Remove [ and ]
                    current_prompt = []
                
                elif line.strip().startswith('#') or line.strip().startswith('==='):
                    # Skip comments and separators
                    continue
                
                elif current_key:
                    # Add line to current prompt
                    current_prompt.append(line)
            
            # Save the last prompt
            if current_key:
                self.prompts[current_key] = '\n'.join(current_prompt).strip()
            
            logger.info(f"Loaded {len(self.prompts)} prompts from {self.prompts_file}")
            
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}")
            self._load_default_prompts()
    
    def _load_default_prompts(self):
        """Load default prompts as fallback"""
        logger.warning("Loading default prompts as fallback")
        
        self.prompts = {
            "main_prompt": """You are a tool selector AI. Determine which tool should handle the user's question.
Available tools: "weather_query", "rag_search", "none"
User's question: "{user_input}"
Respond with ONLY ONE WORD: weather_query, rag_search, or none""",
            
            "tool_weather_response": """The user asked: "{user_query}"
Weather data: {weather_data}
Provide a natural, conversational response about the weather.""",
            
            "tool_rag_response": """The user asked: "{user_query}"
Document information: {rag_data}
Provide a clear answer based ONLY on the provided information."""
        }
    
    def get_prompt(self, key: str, **kwargs) -> Optional[str]:
        """
        Get a prompt by key and format it with provided arguments
        
        Args:
            key: The prompt key (e.g., 'main_prompt', 'tool_weather_response')
            **kwargs: Variables to format into the prompt
        
        Returns:
            Formatted prompt string, or None if key not found
        """
        prompt_template = self.prompts.get(key)
        
        if not prompt_template:
            logger.error(f"Prompt key '{key}' not found")
            return None
        
        try:
            # Format the prompt with provided variables
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing required variable {e} for prompt '{key}'")
            return prompt_template
        except Exception as e:
            logger.error(f"Error formatting prompt '{key}': {str(e)}")
            return prompt_template
    
    def reload_prompts(self):
        """Reload prompts from file (useful for hot-reloading during development)"""
        logger.info("Reloading prompts from file...")
        self.prompts.clear()
        self._load_prompts()
    
    def list_available_prompts(self) -> list:
        """Get list of all available prompt keys"""
        return list(self.prompts.keys())


# Create global instance
prompt_loader = PromptLoader()
