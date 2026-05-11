"""
Configuration module — loads environment variables from .env file.
Exposes Azure AI Foundry credentials and other configuration constants.
"""

from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
# Explicitly specify the path to .env file in the project root
env_file_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file_path)

# Azure AI Foundry credentials
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_MODEL_NAME = os.getenv("AZURE_MODEL_NAME")

# Validate that required settings are present
def validate_settings():
    """
    Validates that all required settings are configured.
    Raises ValueError if any required setting is missing.
    """
    missing = []
    
    if not AZURE_ENDPOINT:
        missing.append("AZURE_ENDPOINT")
    if not AZURE_API_KEY:
        missing.append("AZURE_API_KEY")
    if not AZURE_MODEL_NAME:
        missing.append("AZURE_MODEL_NAME")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
