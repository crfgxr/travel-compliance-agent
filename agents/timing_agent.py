from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json

# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================


class TimingViolation(BaseModel):
    """Model for timing compliance violations"""

    flight_number: str = Field(description="Flight number (e.g., XQ141)")
    reason: str = Field(description="Clear explanation of why this violates the rule")
    departure_date: str = Field(description="Actual departure date/time")
    arrival_date: str = Field(description="Actual arrival date/time")
    approved_period: str = Field(description="Approved travel period dates")
    issue_type: str = Field(
        description="Type of issue: departure_too_early|arrival_too_late|departure_too_late|arrival_too_early"
    )


class TimingDetails(BaseModel):
    """Model for timing compliance details"""

    violations: List[TimingViolation] = Field(
        default=[], description="List of timing violations found"
    )


class TimingComplianceResult(BaseModel):
    """Model for timing compliance check result"""

    rule_name: str = Field(
        default="Flight Ticket Timing", description="Name of the compliance rule"
    )
    status: str = Field(description="Compliance status: COMPLIANT or NON_COMPLIANT")
    message: str = Field(description="Brief summary of findings for the user")
    details: TimingDetails = Field(description="Detailed violation information")


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

Analyze the data and provide your response:
- Set status to "NON_COMPLIANT" if violations found, "COMPLIANT" if no violations
- Write violation reasons in clear, user-friendly language
- Explain exactly what rule was broken and why
- Provide actionable recommendations
- If compliant, return empty violations array
"""


class TimingAgent:
    def __init__(self, llm):
        self.llm = llm
        # Create structured output LLM
        self.structured_llm = llm.with_structured_output(TimingComplianceResult)

    def check_timing_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if flight times fall within travel approval dates using LLM with structured output"""

        system_message = SystemMessage(
            content="You are a travel compliance expert. Analyze travel data and provide compliance assessments using the structured output format."
        )

        # Generate prompt using centralized rules
        user_prompt = get_timing_compliance_prompt(
            json.dumps(travel_approval, indent=2),
            json.dumps(flight_reservations, indent=2),
        )

        human_message = HumanMessage(content=user_prompt)

        try:
            # Use structured output - this will automatically return a TimingComplianceResult object
            result = self.structured_llm.invoke([system_message, human_message])

            # Convert Pydantic model to dictionary for compatibility with existing code
            return result.model_dump()

        except Exception as e:
            # Return error in the expected format
            return {
                "rule_name": "Flight Ticket Timing",
                "status": "SYSTEM_ERROR",
                "message": f"System error during timing compliance check: {str(e)}",
                "details": {
                    "violations": [],
                    "error_type": "llm_call_error",
                    "error_message": str(e),
                },
            }
