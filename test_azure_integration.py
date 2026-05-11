#!/usr/bin/env python3
"""
Test script to verify Azure Foundry GPT-5.4 integration.
Validates that the LLM client can communicate with Azure.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from llm.client import get_azure_client

def test_azure_connection():
    """Tests the Azure LLM connection."""
    
    print("=" * 60)
    print("🧪 TNA Tool — Azure Foundry Integration Test")
    print("=" * 60)
    
    # 1. Validate settings
    print("\n1️⃣  Checking environment variables...")
    try:
        settings.validate_settings()
        print(f"   ✓ AZURE_ENDPOINT: {settings.AZURE_ENDPOINT[:50]}...")
        print(f"   ✓ AZURE_API_KEY: {'*' * 20}...")
        print(f"   ✓ AZURE_MODEL_NAME: {settings.AZURE_MODEL_NAME}")
    except ValueError as e:
        print(f"   ✗ Missing configuration: {e}")
        return False
    
    # 2. Initialize client
    print("\n2️⃣  Initializing Azure LLM client...")
    try:
        client = get_azure_client()
        print(f"   ✓ Client initialized for model: {client.model_name}")
    except Exception as e:
        print(f"   ✗ Failed to initialize client: {e}")
        return False
    
    # 3. Test simple prompt
    print("\n3️⃣  Sending test prompt to GPT-5.4...")
    
    system_prompt = """
    Du är en hjälpsam assistent som svarar kort på svenska.
    """
    
    user_message = "Hej! Kan du bekräfta att du är GPT-5.4?"
    
    try:
        response = client.send_prompt(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.3,
            max_tokens=100
        )
        
        if response:
            print(f"   ✓ Response received ({len(response)} characters)")
            print(f"\n   Svar från GPT-5.4:")
            print(f"   ---")
            print(f"   {response}")
            print(f"   ---")
        else:
            print(f"   ✗ No response from model")
            return False
    
    except Exception as e:
        print(f"   ✗ Failed to send prompt: {e}")
        return False
    
    # 4. Test JSON response
    print("\n4️⃣  Testing JSON response parsing...")
    
    json_prompt = """
    Returnera ENDAST denna JSON utan förklaringar:
    {"status": "ok", "model": "gpt-5.4", "test": true}
    """
    
    try:
        json_response = client.send_prompt_for_json(
            system_prompt="Du returnerar endast giltigt JSON.",
            user_message=json_prompt,
            temperature=0.1,
            max_tokens=100
        )
        
        if json_response:
            print(f"   ✓ JSON parsed successfully")
            print(f"   Status: {json_response.get('status')}")
            print(f"   Model: {json_response.get('model')}")
        else:
            print(f"   ✗ Failed to parse JSON response")
            return False
    
    except Exception as e:
        print(f"   ✗ JSON parsing failed: {e}")
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("✅ Alla tester godkända! Azure Foundry GPT-5.4 är konfigurerad korrekt.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_azure_connection()
    sys.exit(0 if success else 1)
