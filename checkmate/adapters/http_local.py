"""HTTP Local adapter for connecting to local model servers"""

from typing import List, Dict, Any, Optional
import requests
import json
from .base import Adapter, Conversation, Generation


class HTTPLocalAdapter(Adapter):
    """Adapter for local HTTP model servers"""
    
    def __init__(
        self, 
        name: str = "http_local",
        base_url: str = "http://localhost:8000",
        model_name: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self._session = None
    
    def _get_session(self) -> requests.Session:
        """Get or create a requests session"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        return self._session
    
    def generate(self, prompt: str, generations_this_call: int = 1) -> List[str]:
        """Generate responses using the HTTP model server.
        
        Args:
            prompt: The prompt string to send to the model
            generations_this_call: Number of generations to request
            
        Returns:
            List of generated response strings
        """
        session = self._get_session()
        
        # Prepare chat completions payload
        chat_payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }
        
        # Prepare completions payload
        completion_payload = {
            "prompt": prompt,
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }
        
        # Add model name if specified
        if self.model_name:
            chat_payload["model"] = self.model_name
            completion_payload["model"] = self.model_name
        
        try:
            # Try chat completions endpoints first (more common)
            chat_endpoints = [
                f"{self.base_url}/v1/chat/completions",
                f"{self.base_url}/chat/completions"
            ]
            
            # Try completions endpoints  
            completion_endpoints = [
                f"{self.base_url}/v1/completions",
                f"{self.base_url}/completions",
                f"{self.base_url}/generate"
            ]
            
            response = None
            used_payload = None
            
            # Try chat completions first
            for endpoint in chat_endpoints:
                try:
                    response = session.post(
                        endpoint,
                        json=chat_payload,
                        timeout=30
                    )
                    if response.status_code == 200:
                        used_payload = "chat"
                        break
                except requests.exceptions.RequestException:
                    continue
            
            # If chat didn't work, try completions
            if response is None or response.status_code != 200:
                for endpoint in completion_endpoints:
                    try:
                        response = session.post(
                            endpoint,
                            json=completion_payload,
                            timeout=30
                        )
                        if response.status_code == 200:
                            used_payload = "completion"
                            break
                    except requests.exceptions.RequestException:
                        continue
            
            if response is None or response.status_code != 200:
                error_msg = f"Failed to connect to any endpoint."
                if response:
                    try:
                        error_data = response.json()
                        error_msg += f" Server response: {error_data}"
                    except:
                        error_msg += f" Status: {response.status_code}, Body: {response.text[:200]}"
                raise RuntimeError(error_msg)
            
            # Parse response
            response_data = response.json()
            
            # Handle different response formats and return strings
            outputs = []
            if "choices" in response_data:
                # OpenAI-compatible format
                choices = response_data["choices"]
                for choice in choices[:generations_this_call]:
                    text = choice.get("text", choice.get("message", {}).get("content", ""))
                    outputs.append(str(text))
            elif "generated_text" in response_data:
                # Hugging Face format
                text = response_data["generated_text"]
                outputs.append(str(text))
            elif "output" in response_data:
                # Simple format
                text = response_data["output"]
                outputs.append(str(text))
            else:
                # Fallback - try to extract text from response
                text = str(response_data)
                outputs.append(text)
            
            # Return the requested number of generations
            return outputs if outputs else [""]
                
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")
    
    def is_available(self) -> bool:
        """Check if the adapter is available.
        
        Returns:
            True if the server is reachable, False otherwise
        """
        try:
            session = self._get_session()
            # Try health endpoint first
            response = session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        
        try:
            # Try a simple ping to the base URL
            session = self._get_session()
            response = session.get(self.base_url, timeout=5)
            return response.status_code in [200, 404, 405, 500]  # 404/405/500 means server is up but endpoint doesn't exist
        except Exception as e:
            print(f"   ⚠️  Connection failed: {e}")
            return False
