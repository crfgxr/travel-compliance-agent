import json
import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)


def get_openai_key_from_env() -> str:
    """Get OpenAI API key from environment variables"""
    return os.getenv("OPENAI_API_KEY", "")


def is_api_key_available() -> bool:
    """Check if OpenAI API key is available from environment"""
    env_key = get_openai_key_from_env()
    if env_key:
        logger.info("🔑 Found OpenAI API key in environment variables")
        return True
    return False


def validate_openai_key(api_key: str) -> bool:
    """Validate OpenAI API key by making a simple request"""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        # Make a simple request to validate the key
        client.models.list()
        return True
    except Exception as e:
        error_msg = f"Invalid OpenAI API key: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False


def parse_json_input(json_str: str) -> Dict[str, Any]:
    """Parse and validate JSON input"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return None


def extract_data_from_json(travel_data: dict, ticket_data: dict) -> tuple:
    """Extract data from JSON structures for LLM processing"""
    try:
        # Extract travel approval data
        travel_approval = travel_data.get("data", travel_data)

        # Extract flight reservations data
        if "data" in ticket_data and "flights" in ticket_data["data"]:
            flight_reservations = ticket_data["data"]["flights"]
        else:
            flight_reservations = ticket_data.get("flights", [])

        return travel_approval, flight_reservations
    except Exception as e:
        error_msg = f"Error extracting data from JSON: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return None, None


# v0.2 refactored - UI functions moved to ui/common.py
