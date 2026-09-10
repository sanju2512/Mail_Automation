import os
import time
from typing import List, Dict, Any, Optional
from groq import Groq
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LLMServiceError(Exception):
    """Exception raised when LLM generation fails or times out."""
    pass

class LLMService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.client: Optional[Groq] = None
        
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                self.client = Groq(api_key=self.api_key, timeout=settings.GROQ_TIMEOUT)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """
        Invoke GroqCloud LLM with retry support and structured parameter control.
        """
        if not self.client:
            raise LLMServiceError("Groq client is not initialized. Please verify GROQ_API_KEY in .env.")

        temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        max_t = max_tokens if max_tokens is not None else settings.GROQ_MAX_TOKENS

        retries = 3
        backoff = 2

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Invoking Groq model '{self.model}' (attempt {attempt}/{retries})...")
                
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_t,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                return content.strip()

            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Groq API call failed (attempt {attempt}/{retries}): {err_msg}")
                if attempt == retries:
                    raise LLMServiceError(f"GroqCloud LLM request failed after {retries} attempts: {err_msg}")
                time.sleep(backoff * attempt)

        raise LLMServiceError("LLM generation failed unexpectedly.")

# Global shared instance
llm_service = LLMService()
