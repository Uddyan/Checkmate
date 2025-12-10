"""HTTP Local Generator - for local LLM servers

Connects to local HTTP servers running LLMs (like LM Studio, Ollama, etc.)
"""

import json
import logging
from typing import List, Union
import requests
import backoff

from checkmate import _config
from checkmate.attempt import Message, Conversation
from checkmate.exception import RateLimitHit, GarakBackoffTrigger
from checkmate.generators.base import Generator


class HttpLocalGenerator(Generator):
    """Generator for local HTTP LLM servers
    
    Supports OpenAI-compatible APIs and standard completion endpoints
    """
    
    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "uri": "http://localhost:1234",
        "max_tokens": 150,
        "temperature": 0.7,
        "request_timeout": 30,
    }
    
    generator_family_name = "HTTP_LOCAL"
    supports_multiple_generations = False
    
    def __init__(self, uri=None, config_root=_config):
        """Initialize HTTP Local generator
        
        Args:
            uri: Base URL of the local LLM server
            config_root: Configuration root
        """
        self.uri = uri or "http://localhost:1234"
        self.name = self.uri
        self._session = None
        
        # Load configuration
        self._load_config(config_root)
        
        if not hasattr(self, 'max_tokens'):
            self.max_tokens = 150
        if not hasattr(self, 'temperature'):
            self.temperature = 0.7
        if not hasattr(self, 'request_timeout'):
            self.request_timeout = 30
            
        super().__init__(self.name, config_root=config_root)
    
    def _get_session(self) -> requests.Session:
        """Get or create requests session"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        return self._session
    
    @backoff.on_exception(
        backoff.fibo, (RateLimitHit, GarakBackoffTrigger), max_value=70
    )
    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Union[Message, None]]:
        """Call the local HTTP LLM server
        
        Args:
            prompt: Conversation object containing the prompt
            generations_this_call: Number of generations (currently only 1 supported)
            
        Returns:
            List containing a single Message or None
        """
        session = self._get_session()
        
        # Extract prompt text from conversation
        prompt_text = prompt.last_message().text
        
        # Prepare chat completions payload (OpenAI-compatible)
        chat_payload = {
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        # Prepare completions payload (for non-chat endpoints)
        completion_payload = {
            "prompt": prompt_text,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        # Try different endpoint patterns
        # FOR LM STUDIO: Try completions FIRST (chat completions not supported)
        completion_endpoints = [
            f"{self.uri}/v1/completions",
            f"{self.uri}/completions",
            f"{self.uri}/generate"
        ]
        
        chat_endpoints = [
            f"{self.uri}/v1/chat/completions",
            f"{self.uri}/chat/completions"
        ]
        
        response = None
        
        # Try COMPLETIONS first (works for LM Studio & most local servers)
        for endpoint in completion_endpoints:
            try:
                response = session.post(
                    endpoint,
                    json=completion_payload,
                    timeout=self.request_timeout
                )
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException as e:
                logging.debug(f"Completion endpoint {endpoint} failed: {e}")
                continue
        
        # If completions didn't work, try chat completions
        if response is None or response.status_code != 200:
            for endpoint in chat_endpoints:
                try:
                    response = session.post(
                        endpoint,
                        json=chat_payload,
                        timeout=self.request_timeout
                    )
                    if response.status_code == 200:
                        break
                except requests.exceptions.RequestException as e:
                    logging.debug(f"Chat endpoint {endpoint} failed: {e}")
                    continue
        
        # Check if we got a valid response
        if response is None or response.status_code != 200:
            error_msg = f"Failed to connect to {self.uri}"
            if response:
                error_msg += f" - Status: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text[:200]}"
            logging.error(error_msg)
            return [None]
        
        # Parse response
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {e}")
            return [None]
        
        # Extract text from different response formats
        text = None
        
        if "choices" in response_data and len(response_data["choices"]) > 0:
            # OpenAI-compatible format
            choice = response_data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                text = choice["message"]["content"]
            elif "text" in choice:
                text = choice["text"]
        elif "generated_text" in response_data:
            # Hugging Face format
            text = response_data["generated_text"]
        elif "output" in response_data:
            # Simple format
            text = response_data["output"]
        elif "response" in response_data:
            # Alternative simple format
            text = response_data["response"]
        
        if text is None:
            logging.warning(f"Could not extract text from response: {response_data}")
            return [None]
        
        return [Message(str(text))]


DEFAULT_CLASS = "HttpLocalGenerator"
