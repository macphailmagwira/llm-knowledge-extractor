import logging
import time
import os
import json
from typing import Dict, Any, Optional, List, Literal, Union
from dataclasses import dataclass
import asyncio
import random

# Azure OpenAI imports
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from openai import RateLimitError, APITimeoutError, APIConnectionError, InternalServerError, APIStatusError

# Azure AI Inference imports
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError

from llm_knowledge_extractor.core.config import settings
from llm_knowledge_extractor.common.utils.get_logger import get_logger
logger = get_logger() 


class LLMTimeoutError(Exception):
    pass

class AzureLLMClient:
   
    # Model configuration mapping
    MODEL_CONFIG = {
        'gpt4o': {
            'api_type': 'azure_openai',
            'endpoint': 'AZURE_OPENAI_GPT_4O_ENDPOINT',
            'api_key': 'AZURE_OPENAI_GPT_4O_API_KEY',
            'api_version': 'AZURE_OPENAI_GPT_4O_API_VERSION',
            'model_name': 'AZURE_OPENAI_GPT_4O_MODEL_NAME',
            'deployment_name': 'AZURE_OPENAI_GPT_4O_DEPLOYMENT_NAME'
        }
      }
    
    def __init__(self, model: str = 'gpt4o', default_timeout: float = 120.0):
        """Initialize the LLM service with the specified model.
        
        Args:
            model: The model to use Defaults to 'gpt4o'.
            default_timeout: Default timeout in seconds for LLM calls. Defaults to 120 seconds.
        """
        if model not in self.MODEL_CONFIG:
            raise ValueError(f"Unsupported model: {model}. Available models: {list(self.MODEL_CONFIG.keys())}")
        
        self.model = model
        self.model_config = self.MODEL_CONFIG[model]
        self.api_type = self.model_config['api_type']
        self.model_name = getattr(settings, self.model_config['model_name'])
        self.default_timeout = default_timeout
        
        # Initialize the appropriate client based on API type
        if self.api_type == 'azure_openai':
            self.client = AzureOpenAI(
                azure_endpoint=getattr(settings, self.model_config['endpoint']).rstrip('/'),
                api_key=getattr(settings, self.model_config['api_key']),
                api_version=getattr(settings, self.model_config['api_version']),
                timeout=120  # Set client-level timeout to 120 seconds
            )
            # For Azure OpenAI, we need the deployment name for API calls
            self.deployment_name = getattr(settings, self.model_config['deployment_name'])
            
        elif self.api_type == 'azure_ai_inference':
            endpoint = getattr(settings, self.model_config['endpoint'])
            logger.info(f"Initializing Azure AI Inference client for {model} with endpoint: {endpoint}")
            
            self.client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(getattr(settings, self.model_config['api_key']))
             )
        
    def _build_messages_openai(self, prompt: str, system_prompt: str = None) -> List[Dict[str, str]]:
        """Build messages array for Azure OpenAI API call"""
        messages = []

        # Add system prompt if provided, otherwise use default
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            raise ValueError("System prompt is required for Azure OpenAI API calls")
            
        # Add main prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages

    def _build_messages_ai_inference(self, prompt: str, system_prompt: str = None) -> List[Union[SystemMessage, UserMessage, AssistantMessage]]:
        """Build messages array for Azure AI Inference API call"""
        messages = []

        # Add system prompt if provided, otherwise use default
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        else:
            raise ValueError("System prompt is required for Azure AI Inference API calls")
            
        # Add main prompt
        messages.append(UserMessage(content=prompt))
        
        return messages

    async def _call_openai_with_timeout(self, request_params: Dict[str, Any], timeout: float) -> ChatCompletion:
        """Call the Azure OpenAI API with a manual timeout wrapper"""
        try:
            # Create a task for the LLM call
            llm_task = asyncio.create_task(
                asyncio.to_thread(self.client.chat.completions.create, **request_params)
            )            
            # Wait for either the task to complete or timeout
            response = await asyncio.wait_for(llm_task, timeout=timeout)

            return response
            
        except asyncio.TimeoutError:
            # Cancel the task if it's still running
            if not llm_task.done():
                llm_task.cancel()
                try:
                    await llm_task
                except asyncio.CancelledError:
                    pass
            raise LLMTimeoutError(f"LLM call timed out after {timeout} seconds")

    async def _call_ai_inference_with_timeout(self, request_params: Dict[str, Any], timeout: float):
        """Call the Azure AI Inference API with a manual timeout wrapper"""
        try:
            # Create a task for the LLM call
            llm_task = asyncio.create_task(
                asyncio.to_thread(self.client.complete, **request_params)
            )
            
            # Wait for either the task to complete or timeout
            response = await asyncio.wait_for(llm_task, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            # Cancel the task if it's still running
            if not llm_task.done():
                llm_task.cancel()
                try:
                    await llm_task
                except asyncio.CancelledError:
                    pass
            raise LLMTimeoutError(f"LLM call timed out after {timeout} seconds")

    async def call_llm(self, prompt: str, system_prompt: str = None,     
                      temperature: float = 0, max_tokens: int = 4000,
                      response_format: Optional[Literal["text", "json"]] = "text",
                      max_retries: int = 3,
                      timeout: Optional[float] = None) -> str:
        """
        Call the LLM with the given prompt and optional validation feedback, with retry logic and timeout
        
        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            response_format: Format of the response - "text" or "json"
            max_retries: Maximum number of retry attempts for connection errors
            timeout: Timeout in seconds for the LLM call. If None, uses default_timeout
        
        Returns:
            LLM response content
        
        Raises:
            Exception: If the LLM call fails after all retries or returns invalid content
        """
        if timeout is None:
            timeout = self.default_timeout
            
        logger.debug("Calling %s API with timeout: %.1f seconds", self.api_type, timeout)        
        for attempt in range(max_retries + 1):
            try:
                logger.debug("Sending prompt to LLM (length: %d) - Attempt %d/%d (timeout: %.1fs)", 
                           len(prompt), attempt + 1, max_retries + 1, timeout)
                
                if self.api_type == 'azure_openai':
                    # Build messages for OpenAI format
                    messages = self._build_messages_openai(prompt, system_prompt)
                    
                    # Prepare request parameters
                    request_params = {
                        "model": self.model_name,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                    
                    # Add response format if JSON is requested
                    if response_format == "json":
                        request_params["response_format"] = {"type": "json_object"}                     
                    # Call OpenAI API with timeout wrapper
                    response = await self._call_openai_with_timeout(request_params, timeout)
                    content = response.choices[0].message.content
                
                elif self.api_type == 'azure_ai_inference':
                    # Build messages for AI Inference format
                    messages = self._build_messages_ai_inference(prompt, system_prompt)
                    
                    # Prepare request parameters
                    request_params = {
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "model": self.model_name,
                    }
                    
                    # Note: Azure AI Inference may not support response_format in the same way
                    # If JSON is requested, we add it to the system prompt
                    if response_format == "json":
                        if messages and isinstance(messages[0], SystemMessage):
                            if "output JSON" not in messages[0].content:
                                messages[0] = SystemMessage(content=messages[0].content + " Respond with a valid JSON object.")
                    
                    # Call AI Inference API with timeout wrapper
                    response = await self._call_ai_inference_with_timeout(request_params, timeout)
                    content = response.choices[0].message.content

             
                return content.strip()
            
            except Exception as e:
                raise e
 
azure_llm_client = AzureLLMClient()