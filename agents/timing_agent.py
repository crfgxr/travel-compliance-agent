from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List
import json

# =============================================================================
# TIMING COMPLIANCE RULES
# =============================================================================

TIMING_RULES = [
    "All flight departures must occur on or after the travel start date/time (travelBeginDate) and on or before the travel end date/time (travelEndDate) - endpoints are INCLUSIVE",
    "All flight arrivals must occur on or after the travel start date/time (travelBeginDate) and on or before the travel end date/time (travelEndDate) - endpoints are INCLUSIVE",
    "A flight is compliant if: travelBeginDate <= departureDateTime <= travelEndDate AND travelBeginDate <= arrivalDateTime <= travelEndDate",
]

TIMING_RULE_CONFIG = {
    "rule_name": "Flight Ticket Timing",
    "description": "Check if flight times fall within the approved travel period",
    "violation_types": [
        "departure_too_early",
        "arrival_too_late",
        "departure_too_late",
        "arrival_too_early",
    ],
}


def get_timing_compliance_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate prompt for timing compliance check"""

    rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(TIMING_RULES)])

    return f"""
Check if flight times fall within the approved travel period using INCLUSIVE date comparisons.

Travel Approval Data:
{travel_approval}

Flight Reservations Data:
{flight_reservations}

Rules to check:
{rules_text}

IMPORTANT DATE COMPARISON LOGIC:
- Extract travelBeginDate and travelEndDate from travel approval
- For each flight, extract departureDate and arrivalDate
- A flight is COMPLIANT if BOTH conditions are true:
  1. travelBeginDate <= departureDate <= travelEndDate (inclusive)
  2. travelBeginDate <= arrivalDate <= travelEndDate (inclusive)
- Dates should be compared as ISO datetime strings or parsed datetime objects
- If arrival/departure is exactly equal to start/end dates, this is COMPLIANT

EXAMPLE:
Travel Period: 2025-06-22T09:00:00 to 2025-06-26T09:00:00
Flight: Departure 2025-06-24T07:30:00, Arrival 2025-06-24T09:00:00
Result: COMPLIANT (both times are within the inclusive range)

Analyze the data and return a JSON response with this EXACT structure:
{{
    "rule_name": "{TIMING_RULE_CONFIG['rule_name']}",
    "status": "COMPLIANT",
    "message": "Brief summary of findings for the user",
    "details": {{
        "violations": [
            {{
                "flight_number": "flight number (e.g., XQ141)",
                "reason": "Clear explanation of why this violates the rule",
                "departure_date": "actual departure date/time",
                "arrival_date": "actual arrival date/time",
                "approved_period": "approved travel period dates",
                "issue_type": "departure_too_early|arrival_too_late|departure_too_late|arrival_too_early"
            }}
        ]
    }}
}}

Important: 
- Set status to "NON_COMPLIANT" if violations found, "COMPLIANT" if no violations
- Write violation reasons in clear, user-friendly language
- Explain exactly what rule was broken and why
- Provide actionable recommendations
- If compliant, return empty violations array
- MUST return valid JSON object (not array)
- ALWAYS include all required fields: rule_name, status, message, details
"""


class TimingAgent:
    def __init__(self, llm):
        self.llm = llm

    def check_timing_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if flight times fall within travel approval dates using LLM"""

        system_message = SystemMessage(
            content="You are a travel compliance expert. Analyze travel data and provide compliance assessments in JSON format."
        )

        # Generate prompt using centralized rules
        user_prompt = get_timing_compliance_prompt(
            json.dumps(travel_approval, indent=2),
            json.dumps(flight_reservations, indent=2),
        )

        human_message = HumanMessage(content=user_prompt)

        # First, try to call the LLM
        try:
            response = self.llm.invoke([system_message, human_message])
        except Exception as e:
            return {
                "rule_name": "Flight Ticket Timing",
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
                # If it's a list, check if it contains a valid dict
                if (
                    isinstance(result, list)
                    and len(result) > 0
                    and isinstance(result[0], dict)
                ):
                    result = result[0]  # Use the first dict in the list
                else:
                    return {
                        "rule_name": "Flight Ticket Timing",
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
                result["rule_name"] = "Flight Ticket Timing"

            return result
        except (json.JSONDecodeError, TypeError) as e:
            return {
                "rule_name": "Flight Ticket Timing",
                "status": "json_parse_error",
                "message": "Failed to parse LLM response as valid JSON",
                "details": {
                    "error_type": "json_parse_error",
                    "error_message": str(e),
                    "raw_response": response.content,
                },
            }
