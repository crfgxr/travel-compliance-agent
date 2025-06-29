from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import json

# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class TimingViolation(BaseModel):
    """Model for timing compliance violations"""

    flight_number: str = Field(description="Flight number")
    reason: str = Field(description="Why this violates timing rules")
    departure_date: str = Field(description="Flight departure date/time")
    arrival_date: str = Field(description="Flight arrival date/time")
    approved_period: str = Field(description="Approved travel period")


class TimingComplianceResult(BaseModel):
    """Model for timing compliance check result"""

    rule_name: str = Field(
        default="Flight Ticket Timing", description="Name of the compliance rule"
    )
    status: str = Field(description="COMPLIANT or NON_COMPLIANT")
    message: str = Field(description="Brief summary for user")
    violations: List[TimingViolation] = Field(
        default=[], description="List of violations"
    )


# =============================================================================
# RULES
# =============================================================================

TIMING_RULE = "Flight departures and arrivals must occur within the approved travel period (travelBeginDate to travelEndDate, inclusive)"


def get_timing_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate simplified prompt for timing compliance check"""
    return f"""
Check if flight times fall within the approved travel period.

Rule: {TIMING_RULE}

Travel Approval: {json.dumps(travel_approval, indent=2)}
Flight Reservations: {json.dumps(flight_reservations, indent=2)}

Compare each flight's departure and arrival times against travelBeginDate and travelEndDate.
Set status to "NON_COMPLIANT" if any violations found, otherwise "COMPLIANT".
"""


class TimingAgent:
    def __init__(self, llm):
        self.llm = llm
        self.structured_llm = llm.with_structured_output(TimingComplianceResult)

    def check_timing_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        system_message = SystemMessage(
            content="You are a travel compliance expert. Check timing compliance and return structured results."
        )

        user_prompt = get_timing_prompt(travel_approval, flight_reservations)
        human_message = HumanMessage(content=user_prompt)

        try:
            result = self.structured_llm.invoke([system_message, human_message])
            return result.model_dump()
        except Exception as e:
            return {
                "rule_name": "Flight Ticket Timing",
                "status": "SYSTEM_ERROR",
                "message": f"System error during timing check: {str(e)}",
                "violations": [],
            }
