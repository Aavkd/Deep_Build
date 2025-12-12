"""
LLM Service - Ollama Client Wrapper

Provides a wrapper around the Ollama Python client for LLM inference.
Supports configurable models, system prompts, and context truncation.
"""

import ollama
from typing import Optional


class LLMService:
    """
    Wrapper around Ollama client for LLM text generation.
    
    Attributes:
        model: The Ollama model to use (default: granite4:3b)
        max_context_chars: Maximum characters for context truncation
    """
    
    def __init__(
        self, 
        model: str = "granite4:3b",
        max_context_chars: int = 100000,
        ollama_host: Optional[str] = None
    ):
        """
        Initialize the LLM service.
        
        Args:
            model: Ollama model name (default: granite4:3b)
            max_context_chars: Maximum context window in characters
            ollama_host: Optional Ollama server URL (default: localhost:11434)
        """
        self.model = model
        self.max_context_chars = max_context_chars
        
        # Initialize Ollama client
        if ollama_host:
            self.client = ollama.Client(host=ollama_host)
        else:
            self.client = ollama.Client()
    
    def _truncate_text(self, text: str, max_chars: int) -> str:
        """
        Truncate text to fit within context limits.
        
        Args:
            text: Input text to truncate
            max_chars: Maximum character count
            
        Returns:
            Truncated text with indicator if truncated
        """
        if len(text) <= max_chars:
            return text
        
        truncated = text[:max_chars]
        # Try to cut at a sentence boundary
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        cut_point = max(last_period, last_newline)
        
        if cut_point > max_chars * 0.8:  # Only use natural boundary if reasonable
            truncated = truncated[:cut_point + 1]
        
        return truncated + "\n\n[... Content truncated due to length ...]"
    
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using the LLM with system and user prompts.
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User query/content to process
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (optional)
            
        Returns:
            Generated text response from the LLM
            
        Raises:
            Exception: If Ollama API call fails
        """
        # Truncate prompts if needed to fit context window
        total_chars = len(system_prompt) + len(user_prompt)
        
        if total_chars > self.max_context_chars:
            # Prioritize system prompt, truncate user prompt more aggressively
            system_chars = min(len(system_prompt), self.max_context_chars // 4)
            user_chars = self.max_context_chars - system_chars
            
            system_prompt = self._truncate_text(system_prompt, system_chars)
            user_prompt = self._truncate_text(user_prompt, user_chars)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options
            )
            
            return response["message"]["content"]
            
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def generate_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ):
        """
        Generate text using the LLM with streaming response.
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User query/content to process
            temperature: Sampling temperature (0.0-1.0)
            
        Yields:
            Text chunks as they are generated
        """
        # Truncate prompts if needed
        total_chars = len(system_prompt) + len(user_prompt)
        
        if total_chars > self.max_context_chars:
            system_chars = min(len(system_prompt), self.max_context_chars // 4)
            user_chars = self.max_context_chars - system_chars
            
            system_prompt = self._truncate_text(system_prompt, system_chars)
            user_prompt = self._truncate_text(user_prompt, user_chars)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": temperature}
            )
            
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            raise Exception(f"LLM streaming failed: {str(e)}")
    
    def check_connection(self) -> bool:
        """
        Check if Ollama server is accessible and model is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # List models to verify connection
            models_response = self.client.list()
            
            # Handle both old dict format and new Model object format
            models = models_response.get("models", []) if isinstance(models_response, dict) else getattr(models_response, 'models', [])
            
            model_names = []
            for m in models:
                # Handle both dict and Model object formats
                if isinstance(m, dict):
                    name = m.get("name", "")
                else:
                    name = getattr(m, 'model', getattr(m, 'name', ''))
                model_names.append(name)
            
            # Check if our model is available (with or without tag)
            base_model = self.model.split(":")[0]
            for name in model_names:
                if name and name.startswith(base_model):
                    return True
            
            # Model not found but connection works
            return True
            
        except Exception:
            return False
