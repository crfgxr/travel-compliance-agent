from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import logging

# Setup logger
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================


class IdentityViolation(BaseModel):
    """Model for identity compliance violations"""

    passenger_name: str = Field(description="Passenger name from ticket")
    reason: str = Field(
        description="Clear explanation of why this passenger is not compliant"
    )
    ticket_employee_id: Optional[str] = Field(
        default=None, description="Employee ID from flight ticket"
    )
    approved_employee_id: Optional[str] = Field(
        default=None, description="Employee ID from travel approval (if exists)"
    )
    booking_reference: str = Field(description="Booking ID or confirmation number")
    issue_type: str = Field(
        description="Type of issue: name_mismatch|employee_id_mismatch|unauthorized_passenger|missing_approval"
    )
    expected_name: Optional[str] = Field(
        default=None, description="Correct name from approval (if applicable)"
    )


class IdentityDetails(BaseModel):
    """Model for identity compliance details"""

    violations: List[IdentityViolation] = Field(
        default=[], description="List of identity violations found"
    )


class IdentityComplianceResult(BaseModel):
    """Model for identity compliance check result"""

    rule_name: str = Field(
        default="Passenger Identity", description="Name of the compliance rule"
    )
    status: str = Field(description="Compliance status: COMPLIANT or NON_COMPLIANT")
    message: str = Field(description="Brief summary of findings for the user")
    details: IdentityDetails = Field(description="Detailed violation information")


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

Analyze the data and provide your response:
- Set status to "NON_COMPLIANT" if violations found, "COMPLIANT" if no violations
- Write violation reasons in clear, user-friendly language
- Explain exactly what identity issue was found
- Show what was expected vs what was found
- Provide specific steps to resolve each issue
- If compliant, return empty violations array
"""


class IdentityAgent:
    def __init__(self, llm):
        self.llm = llm
        # Create structured output LLM
        self.structured_llm = llm.with_structured_output(IdentityComplianceResult)

    def check_passenger_identity(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check passenger name consistency between approval and reservations using LLM with structured output"""

        system_message = SystemMessage(
            content="You are a travel compliance expert. Analyze passenger identity data and provide compliance assessments using the structured output format."
        )

        # Generate prompt using centralized rules
        user_prompt = get_passenger_identity_prompt(
            json.dumps(travel_approval, indent=2),
            json.dumps(flight_reservations, indent=2),
        )

        human_message = HumanMessage(content=user_prompt)

        try:
            # Use structured output - this will automatically return an IdentityComplianceResult object
            result = self.structured_llm.invoke([system_message, human_message])

            # Convert Pydantic model to dictionary for compatibility with existing code
            return result.model_dump()

        except Exception as e:
            # Return error in the expected format
            return {
                "rule_name": "Passenger Identity",
                "status": "SYSTEM_ERROR",
                "message": f"System error during identity compliance check: {str(e)}",
                "details": {
                    "violations": [],
                    "error_type": "llm_call_error",
                    "error_message": str(e),
                },
            }
