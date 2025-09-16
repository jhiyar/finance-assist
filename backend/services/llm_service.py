import os
from abc import ABC, abstractmethod
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_community.llms import GPT4All
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks.manager import CallbackManager
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackManager
from django.conf import settings


class BaseLLMService(ABC):
    """Abstract base class for LLM services."""
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass


class ChatGPTService(BaseLLMService):
    """Service for OpenAI ChatGPT API using LangChain."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", **kwargs):
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', None)
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in Django settings.")
        
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 150)
        )
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using ChatGPT API via LangChain."""
        try:
            messages = [
                SystemMessage(content="You are a helpful financial assistant."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            raise Exception(f"ChatGPT API request failed: {str(e)}")


class LocalLLMService(BaseLLMService):
    """Service for local LLMs using LangChain with GPT4All."""
    
    def __init__(self, model_name: str = "ggml-gpt4all-j-v1.3-groovy", **kwargs):
        self.model_name = model_name
        
        # Set up callback manager for streaming (optional)
        callback_manager = CallbackManager([StreamingStdOutCallbackManager()])
        
        try:
            self.llm = GPT4All(
                model=self.model_name,
                callback_manager=callback_manager,
                verbose=True,
                temp=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 150),
                top_k=kwargs.get('top_k', 40),
                top_p=kwargs.get('top_p', 0.9),
                repeat_penalty=kwargs.get('repeat_penalty', 1.1)
            )
        except Exception as e:
            raise Exception(f"Failed to load local LLM model '{self.model_name}': {str(e)}")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using local LLM via LangChain."""
        if not self.llm:
            raise Exception("Local LLM model not loaded")
        
        try:
            # Add system prompt
            full_prompt = f"You are a helpful financial assistant. {prompt}"
            
            response = self.llm.invoke(full_prompt)
            return response.strip()
            
        except Exception as e:
            raise Exception(f"Local LLM generation failed: {str(e)}")


class LLMServiceFactory:
    """Factory class for creating LLM services."""
    
    @staticmethod
    def create_service(service_type: str, **kwargs) -> BaseLLMService:
        """Create an LLM service based on the specified type."""
        if service_type.lower() == 'chatgpt':
            return ChatGPTService(**kwargs)
        elif service_type.lower() == 'local':
            return LocalLLMService(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM service type: {service_type}")


# Default LLM service instance
def get_default_llm_service() -> BaseLLMService:
    """Get the default LLM service based on Django settings configuration."""
    service_type = getattr(settings, 'LLM_SERVICE_TYPE', 'chatgpt').lower()
    
    if service_type == 'local':
        model_name = getattr(settings, 'LOCAL_LLM_MODEL_NAME', 'ggml-gpt4all-j-v1.3-groovy')
        return LocalLLMService(model_name=model_name)
    else:
        return ChatGPTService()
