#!/usr/bin/env python3
"""
Simpel Azure API-test — testar REST API-anslutningen för GPT-5.4.
"""

import sys
import os

# Lägg till projekt-katalogen i Python-path
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
import dotenv

# Explicit absolute path
env_path = Path(__file__).resolve().parent / ".env"
print(f"[DEBUG] Loading .env from: {env_path}")
print(f"[DEBUG] File exists: {env_path.exists()}")

result = dotenv.load_dotenv(env_path)
print(f"[DEBUG] load_dotenv returned: {result}")

# Hämta uppgifter
endpoint = os.getenv("AZURE_ENDPOINT")
api_key = os.getenv("AZURE_API_KEY")
model_name = os.getenv("AZURE_MODEL_NAME")

print("=" * 60)
print("🧪 Azure Foundry REST API Test för GPT-5.4")
print("=" * 60)

print("\n1️⃣  Kontrollerar miljövariabler...")
if endpoint and api_key and model_name:
    print(f"   ✓ AZURE_ENDPOINT: {endpoint[:50]}...")
    print(f"   ✓ AZURE_API_KEY: {'*' * 20}...")
    print(f"   ✓ AZURE_MODEL_NAME: {model_name}")
else:
    print("   ✗ Någon miljövariabel saknas!")
    sys.exit(1)

print("\n2️⃣  Importerar moduler...")
try:
    from llm.client import AzureLLMClient
    print("   ✓ LLM-klient importerad")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3️⃣  Initialiserar Azure-klient...")
try:
    client = AzureLLMClient()
    print(f"   ✓ Klient initialiserad")
    print(f"   ✓ Endpoint: {client.endpoint}")
    print(f"   ✓ Modell: {client.model_name}")
except Exception as e:
    print(f"   ✗ Kunde inte initialisera klient: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4️⃣  Skickar test-prompt till GPT-5.4 (REST API)...")
try:
    response = client.send_prompt(
        system_prompt="Du är en hjälpsam assistent på svenska.",
        user_message="Hej! Bekräfta att du är GPT-5.4 och att anslutningen fungerar via REST API.",
        temperature=0.3,
        max_tokens=100
    )
    
    if response:
        print(f"   ✓ Svar från GPT-5.4 ({len(response)} tecken)")
        print(f"\n   📝 Svar:")
        print(f"   {response}")
    else:
        print(f"   ✗ Tomt svar från modellen")
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ Fel vid API-anrop: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TEST GODKÄNT! Azure Foundry GPT-5.4 REST API fungerar!")
print("=" * 60)

