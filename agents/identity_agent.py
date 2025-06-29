from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List
import json
import logging

# Setup logger
logger = logging.getLogger(__name__)

# =============================================================================
# PASSENGER IDENTITY RULES
# =============================================================================

PASSENGER_IDENTITY_RULES = [
    "All passengers in flight reservations must be in the approved passenger list",
    "Employee IDs must match between approval and reservations",
    "Names must match exactly (case-insensitive comparison)",
]

PASSENGER_IDENTITY_RULE_CONFIG = {
    "rule_name": "Passenger Identity",
    "description": "Check if passenger identities match between travel approval and flight reservations",
    "violation_types": [
        "name_mismatch",
        "employee_id_mismatch",
        "unauthorized_passenger",
        "missing_approval",
    ],
}


def get_passenger_identity_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate prompt for passenger identity check"""

    rules_text = "\n".join(
        [f"{i+1}. {rule}" for i, rule in enumerate(PASSENGER_IDENTITY_RULES)]
    )

    return f"""
Check if passenger identities match between travel approval and flight reservations.

Travel Approval Data:
{travel_approval}

Flight Reservations Data:
{flight_reservations}

Rules to check:
{rules_text}

Analyze the data and return a JSON response with this EXACT structure:
{{
    "rule_name": "{PASSENGER_IDENTITY_RULE_CONFIG['rule_name']}",
    "status": "COMPLIANT",
    "message": "Brief summary of findings for the user",
    "details": {{
        "violations": [
            {{
                "passenger_name": "passenger name from ticket",
                "reason": "Clear explanation of why this passenger is not compliant",
                "ticket_employee_id": "employee ID from flight ticket",
                "approved_employee_id": "employee ID from travel approval (if exists)",
                "booking_reference": "booking ID or confirmation number",
                "issue_type": "name_mismatch|employee_id_mismatch|unauthorized_passenger|missing_approval",
                "expected_name": "correct name from approval (if applicable)"
            }}
        ]
    }}
}}

Important:
- Set status to "NON_COMPLIANT" if violations found, "COMPLIANT" if no violations
- Write violation reasons in clear, user-friendly language
- Explain exactly what identity issue was found
- Show what was expected vs what was found
- Provide specific steps to resolve each issue
- If compliant, return empty violations array
- MUST return valid JSON object (not array)
- ALWAYS include all required fields: rule_name, status, message, details
"""


class IdentityAgent:
    def __init__(self, llm):
        self.llm = llm

    def check_passenger_identity(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check passenger name consistency between approval and reservations using LLM"""

        system_message = SystemMessage(
            content="You are a travel compliance expert. Analyze passenger identity data and provide compliance assessments in JSON format."
        )

        # Generate prompt using centralized rules
        user_prompt = get_passenger_identity_prompt(
            json.dumps(travel_approval, indent=2),
            json.dumps(flight_reservations, indent=2),
        )

        human_message = HumanMessage(content=user_prompt)

        # First, try to call the LLM
        try:
            response = self.llm.invoke([system_message, human_message])
        except Exception as e:
            return {
                "rule_name": "Passenger Identity",
                "status": "llm_call_error",
                "message": str(e),
                "details": {
                    "error_type": "llm_call_error",
                    "error_message": str(e),
                },
            }

        # Then, try to parse the response as JSON
        try:
            # Handle both string and already parsed content
            if isinstance(response.content, str):
                result = json.loads(response.content)
            else:
                # If content is already a Python object (list/dict), use it directly
                result = response.content

            # Ensure result is a dictionary with required status field
            if not isinstance(result, dict):
                return {
                    "rule_name": "Passenger Identity",
                    "status": "SYSTEM_ERROR",
                    "message": "LLM returned invalid format (expected dictionary, got {})".format(
                        type(result).__name__
                    ),
                    "details": {
                        "error_type": "invalid_format",
                        "raw_response": result,
                    },
                }

            # Ensure status field exists
            if "status" not in result:
                result["status"] = "SYSTEM_ERROR"
                result["message"] = "Missing status field in LLM response"
                result["rule_name"] = "Passenger Identity"

            return result
        except (json.JSONDecodeError, TypeError) as e:
            return {
                "rule_name": "Passenger Identity",
                "status": "json_parse_error",
                "message": "Failed to parse LLM response as valid JSON",
                "details": {
                    "error_type": "json_parse_error",
                    "error_message": str(e),
                    "raw_response": response.content,
                },
            }
