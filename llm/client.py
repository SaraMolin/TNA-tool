"""
LLM client module — communicates with Azure AI Foundry.

Provides a wrapper around the Azure AI Inference client for sending
prompts and receiving structured JSON responses via REST API.
"""

from typing import Optional
import json
import requests

from config import settings


class AzureLLMClient:
    """
    Client for interacting with Azure AI Foundry.
    """
    
    def __init__(self):
        """
        Initializes the Azure LLM client with credentials from settings.
        Raises ValueError if required settings are not configured.
        """
        # Validate settings
        settings.validate_settings()
        
        self.endpoint = settings.AZURE_ENDPOINT.strip()
        self.api_key = settings.AZURE_API_KEY
        self.model_name = settings.AZURE_MODEL_NAME
        
        # Extract base endpoint if it contains full path
        if "/chat/completions" in self.endpoint:
            self.endpoint = self.endpoint.split("/chat/completions")[0]
        if "/openai/deployments" in self.endpoint:
            self.endpoint = self.endpoint.split("/openai/deployments")[0]
        if "?" in self.endpoint:
            self.endpoint = self.endpoint.split("?")[0]
        
        # Ensure no trailing slash
        self.endpoint = self.endpoint.rstrip("/")
    
    def send_prompt(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Sends a prompt to the LLM and returns the response using REST API.
        
        Args:
            system_prompt: system message defining the LLM's role and behavior
            user_message: the main prompt/instruction for the LLM
            temperature: controls randomness (0.0-1.0, lower = more deterministic)
            max_tokens: maximum number of tokens in the response
        
        Returns:
            The LLM's response text, or None if an error occurred
        """
        try:
            # Construct Azure OpenAI REST API URL
            url = f"{self.endpoint}/openai/deployments/{self.model_name}/chat/completions?api-version=2025-01-01-preview"
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_completion_tokens": max_tokens,  # GPT-5.4 parameter
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Azure LLM: {str(e)}")
            print(f"Endpoint: {self.endpoint}")
            print(f"Model: {self.model_name}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"Response: {e.response.json()}")
                except:
                    print(f"Response: {e.response.text}")
            return None
        
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None
    
    def send_prompt_for_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Optional[dict]:
        """
        Sends a prompt and parses the response as JSON.
        
        Args:
            system_prompt: system message defining the LLM's role
            user_message: the main prompt/instruction
            temperature: controls randomness
            max_tokens: maximum tokens in response
        
        Returns:
            Parsed JSON dict, or None if response was not valid JSON
        """
        response_text = self.send_prompt(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response_text is None:
            return None
        
        try:
            # Remove markdown code fences if present
            response_text = response_text.strip()
            
            # Remove code block markers
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Find and extract JSON object (handles cases where LLM adds text before/after JSON)
            # Try to find the first '{' and last '}'
            json_start = response_text.find('{')
            json_end = response_text.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end+1]
            
            response_text = response_text.strip()
            
            # The LLM response may contain unescaped actual newlines in string values.
            # We need to escape these for valid JSON, but we must be careful not to
            # double-escape sequences that are already escaped (like \n in the response).
            # 
            # Strategy: Use a simple approach - only escape actual control characters,
            # assuming the LLM produces valid or nearly-valid JSON with proper escaping.
            # If json.loads fails, we'll retry with more aggressive sanitization.
            
            try:
                parsed = json.loads(response_text)
                return parsed
            except json.JSONDecodeError:
                # First JSON parse failed. Try sanitizing unescaped control characters.
                # Only replace actual newlines/tabs/carriage returns (not already-escaped sequences)
                response_text = response_text.replace('\r\n', '\n')  # Normalize line endings first
                response_text = response_text.replace('\n', '\\n')   # Escape actual newlines
                response_text = response_text.replace('\r', '\\r')   # Escape carriage returns
                response_text = response_text.replace('\t', '\\t')   # Escape tabs
                
                parsed = json.loads(response_text)
                return parsed
        
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {str(e)}")
            print(f"Raw response (first 500 chars): {response_text[:500]}")
            print(f"Full response length: {len(response_text)}")
            return None
        
        except Exception as e:
            print(f"Unexpected error parsing JSON: {str(e)}")
            return None


def get_azure_client() -> AzureLLMClient:
    """
    Factory function to get an initialized Azure LLM client.
    
    Returns:
        Initialized AzureLLMClient instance
    """
    return AzureLLMClient()
