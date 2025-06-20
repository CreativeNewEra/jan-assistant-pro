"""
API client for communicating with Jan.ai and other OpenAI-compatible APIs
"""

import requests
import json
from typing import List, Dict, Any, Optional
import time


class APIClient:
    """Client for interacting with OpenAI-compatible APIs"""
    
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set up default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        })
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       stream: bool = False, 
                       temperature: float = 0.7,
                       max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a chat completion request
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Randomness in the response (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response dictionary from the API
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            raise APIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise APIError("Could not connect to API server. Is Jan running?")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                error_detail = response.json().get('message', 'Unknown error')
                if 'Engine is not loaded' in error_detail:
                    raise APIError("Model is not loaded in Jan. Please start your model first.")
                else:
                    raise APIError(f"Bad request: {error_detail}")
            elif response.status_code == 401:
                raise APIError("Authentication failed. Check your API key.")
            elif response.status_code == 404:
                raise APIError("API endpoint not found. Check your base URL.")
            else:
                raise APIError(f"HTTP {response.status_code}: {response.text}")
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response from server")
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}")
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        url = f"{self.base_url}/models"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            raise APIError(f"Failed to get models: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if the API is healthy"""
        try:
            # Try a simple request
            test_messages = [{"role": "user", "content": "hi"}]
            self.chat_completion(test_messages)
            return True
        except APIError:
            return False
        except Exception:
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return status information"""
        status = {
            'connected': False,
            'model_loaded': False,
            'latency_ms': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Test basic connectivity
            test_messages = [{"role": "user", "content": "ping"}]
            response = self.chat_completion(test_messages)
            
            end_time = time.time()
            status['latency_ms'] = round((end_time - start_time) * 1000, 2)
            status['connected'] = True
            status['model_loaded'] = True
            
        except APIError as e:
            status['error'] = str(e)
            if "not loaded" in str(e).lower():
                status['connected'] = True  # API is reachable but model not loaded
            
        except Exception as e:
            status['error'] = f"Connection failed: {str(e)}"
        
        return status
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extract the content from a chat completion response
        
        Args:
            response: The response dictionary from chat_completion
            
        Returns:
            The text content of the response
        """
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            raise APIError("Invalid response format: missing content")
    
    def extract_reasoning(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Extract reasoning content if available (for models that support it)
        
        Args:
            response: The response dictionary from chat_completion
            
        Returns:
            The reasoning content or None if not available
        """
        try:
            return response['choices'][0]['message'].get('reasoning_content')
        except (KeyError, IndexError):
            return None
    
    def get_usage_stats(self, response: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract usage statistics from response
        
        Args:
            response: The response dictionary from chat_completion
            
        Returns:
            Dictionary with token usage information
        """
        try:
            usage = response.get('usage', {})
            return {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        except Exception:
            return {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass
