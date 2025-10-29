import os
import logging
import ssl
from typing import Optional
import httpx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI LLM and embedding models."""
    
    # Model-specific token limits
    MODEL_TOKEN_LIMITS = {
        'gpt-3.5-turbo': 4096,
        'gpt-3.5-turbo-16k': 16384,
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4o': 128000,
        'gpt-4o-mini': 4096,
        'gpt-4-turbo': 128000,
        'gpt-4-turbo-preview': 128000,
    }
    
    def __init__(self):
        print('OpenAIService initialized', flush=True)

        # Create HTTP client with SSL verification disabled for corporate networks
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create httpx client with custom SSL context
        self.http_client = httpx.Client(
            verify=False,  # Disable SSL verification
            timeout=httpx.Timeout(60.0, connect=10.0)
        )
        
        # Load OpenAI configuration from Django settings
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.model_name = getattr(settings, 'OPENAI_MODEL_NAME', 'gpt-3.5-turbo')
        self.embedding_model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.temperature = float(getattr(settings, 'OPENAI_TEMPERATURE', '0.1'))
        
        # print(f"OpenAI API Key from settings: {self.api_key}", flush=True)
        # print(f"Environment OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}", flush=True)
        
        # Use model-specific token limit or fall back to settings
        default_max_tokens = self.MODEL_TOKEN_LIMITS.get(self.model_name, 4096)
        self.max_tokens = int(getattr(settings, 'OPENAI_MAX_TOKENS', str(default_max_tokens)))
        
        # Ensure max_tokens doesn't exceed model limit
        model_limit = self.MODEL_TOKEN_LIMITS.get(self.model_name, 4096)
        if self.max_tokens > model_limit:
            print(f"Warning: max_tokens ({self.max_tokens}) exceeds model limit ({model_limit}), using {model_limit}", flush=True)
            self.max_tokens = model_limit
        
        print(f"OpenAI API Key found: {'Yes' if self.api_key else 'No'}", flush=True)
        print(f"Model: {self.model_name}, max_tokens: {self.max_tokens}", flush=True)
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
    def get_langchain_llm(self, max_tokens: Optional[int] = None) -> ChatOpenAI:
        """Get a LangChain-compatible OpenAI LLM instance."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required but not set")
        
        # Use provided max_tokens or fall back to the service default
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        # Ensure tokens doesn't exceed model limit
        model_limit = self.MODEL_TOKEN_LIMITS.get(self.model_name, 4096)
        if tokens > model_limit:
            print(f"Warning: max_tokens ({tokens}) exceeds model limit ({model_limit}), using {model_limit}", flush=True)
            tokens = model_limit
        
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=tokens,
            openai_api_key=self.api_key,
            http_client=self.http_client
        )
    
    def get_langchain_embeddings(self) -> OpenAIEmbeddings:
        """Get a LangChain-compatible OpenAI embeddings instance."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required but not set")
        
        return OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=self.api_key,
            http_client=self.http_client
        )


def get_openai_service() -> OpenAIService:
    """Get a default OpenAI service instance."""
    return OpenAIService()
