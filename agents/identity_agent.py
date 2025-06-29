from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import json

# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class IdentityViolation(BaseModel):
    """Model for identity compliance violations"""

    passenger_name: str = Field(description="Passenger name from ticket")
    reason: str = Field(description="Why this violates identity rules")
    booking_reference: str = Field(description="Booking ID or confirmation number")


class IdentityComplianceResult(BaseModel):
    """Model for identity compliance check result"""

    rule_name: str = Field(
        default="Passenger Identity", description="Name of the compliance rule"
    )
    status: str = Field(description="COMPLIANT or NON_COMPLIANT")
    message: str = Field(description="Brief summary for user")
    violations: List[IdentityViolation] = Field(
        default=[], description="List of violations"
    )


# =============================================================================
# RULES
# =============================================================================

IDENTITY_RULE = "All passengers in flight reservations must match the approved passenger list with exact name matching"


def get_identity_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate simplified prompt for identity compliance check"""
    return f"""
Check if passenger identities match between travel approval and flight reservations.

Rule: {IDENTITY_RULE}

Travel Approval: {json.dumps(travel_approval, indent=2)}
Flight Reservations: {json.dumps(flight_reservations, indent=2)}

Compare passenger names between approval and reservations (case-insensitive).
Set status to "NON_COMPLIANT" if any violations found, otherwise "COMPLIANT".
"""


class IdentityAgent:
    def __init__(self, llm):
        self.llm = llm
        self.structured_llm = llm.with_structured_output(IdentityComplianceResult)

    def check_passenger_identity(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check passenger name consistency between approval and reservations"""

        system_message = SystemMessage(
            content="You are a travel compliance expert. Check identity compliance and return structured results."
        )

        user_prompt = get_identity_prompt(travel_approval, flight_reservations)
        human_message = HumanMessage(content=user_prompt)

        try:
            result = self.structured_llm.invoke([system_message, human_message])
            return result.model_dump()
        except Exception as e:
            return {
                "rule_name": "Passenger Identity",
                "status": "SYSTEM_ERROR",
                "message": f"System error during identity check: {str(e)}",
                "violations": [],
            }
