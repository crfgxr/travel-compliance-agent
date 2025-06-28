import json
import streamlit as st
from typing import Dict, Any, List
from datetime import datetime


def validate_openai_key(api_key: str) -> bool:
    """Validate OpenAI API key by making a simple request"""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        # Make a simple request to validate the key
        client.models.list()
        return True
    except Exception as e:
        # Import here to avoid circular imports
        if "toasters" not in st.session_state:
            st.session_state.toasters = []

        # Add error to toasters
        toaster = {
            "id": len(st.session_state.toasters),
            "message": f"Invalid OpenAI API key: {str(e)}",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "visible": True,
        }
        st.session_state.toasters.insert(0, toaster)
        return False


def parse_json_input(json_str: str) -> Dict[str, Any]:
    """Parse and validate JSON input"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Add error to toasters
        if "toasters" not in st.session_state:
            st.session_state.toasters = []

        toaster = {
            "id": len(st.session_state.toasters),
            "message": f"Invalid JSON format: {str(e)}",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "visible": True,
        }
        st.session_state.toasters.insert(0, toaster)
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
        # Add error to toasters
        if "toasters" not in st.session_state:
            st.session_state.toasters = []

        toaster = {
            "id": len(st.session_state.toasters),
            "message": f"Error extracting data from JSON: {str(e)}",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "visible": True,
        }
        st.session_state.toasters.insert(0, toaster)
        return None, None


def format_compliance_result(result: dict) -> str:
    """Format compliance result for display"""
    status_emoji = {
        "COMPLIANT": "✅",
        "NON_COMPLIANT": "❌",
        "WARNING": "⚠️",
    }

    status = result.get("status", "UNKNOWN")
    rule_name = result.get("rule_name", "Unknown Rule")
    message = result.get("message", "No message")

    return f"{status_emoji.get(status, '❓')} **{rule_name}**: {message}"


def create_sample_data() -> tuple:
    """Load sample data from JSON files"""
    try:
        # Load travel approval data from TravelApproval.json
        with open("TravelApproval.json", "r", encoding="utf-8") as f:
            sample_travel_approval = json.load(f)

        # Load ticket data from Ticket.json
        with open("Ticket.json", "r", encoding="utf-8") as f:
            sample_ticket_data = json.load(f)

        return sample_travel_approval, sample_ticket_data

    except FileNotFoundError as e:
        # Add error to toasters
        if "toasters" not in st.session_state:
            st.session_state.toasters = []

        toaster = {
            "id": len(st.session_state.toasters),
            "message": f"Sample data file not found: {str(e)}",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "visible": True,
        }
        st.session_state.toasters.insert(0, toaster)
        return None, None
    except json.JSONDecodeError as e:
        # Add error to toasters
        if "toasters" not in st.session_state:
            st.session_state.toasters = []

        toaster = {
            "id": len(st.session_state.toasters),
            "message": f"Error parsing sample data JSON: {str(e)}",
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "visible": True,
        }
        st.session_state.toasters.insert(0, toaster)
        return None, None
