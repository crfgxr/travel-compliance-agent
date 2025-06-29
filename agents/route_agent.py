from typing import Dict, Any, List
from pydantic import BaseModel, Field
import json
import os

# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class RouteViolation(BaseModel):
    """Model for route compliance violations"""

    flight_number: str = Field(description="Flight number")
    reason: str = Field(description="Why this violates route rules")
    actual_airline: str = Field(description="Airline code that was used")
    route: str = Field(description="Departure -> arrival route")
    booking_reference: str = Field(description="Booking ID or confirmation number")


class RouteComplianceResult(BaseModel):
    """Model for route compliance check result"""

    rule_name: str = Field(
        default="SunExpress Route Compliance", description="Name of the compliance rule"
    )
    status: str = Field(description="COMPLIANT or NON_COMPLIANT")
    message: str = Field(description="Brief summary for user")
    violations: List[RouteViolation] = Field(
        default=[], description="List of violations"
    )


# =============================================================================
# RULES
# =============================================================================

ROUTE_RULE = "Use SunExpress (XQ) when it serves both departure and arrival airports"


def load_sunexpress_destinations() -> set:
    """Load SunExpress destinations from local Amadeus JSON file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "..", "sample_data", "AirlineRoutes.json")

        with open(json_path, "r") as f:
            data = json.load(f)

        # Extract IATA codes from the Amadeus response - ONLY use actual data
        destinations = set()
        for item in data.get("data", []):
            iata_code = item.get("iataCode")
            if iata_code:
                destinations.add(iata_code.upper())

        return destinations
    except Exception as e:
        # Return empty set if file can't be loaded
        return set()


def check_sunexpress_serves_route(
    departure: str, arrival: str, sunexpress_destinations: set
) -> bool:
    """Check if SunExpress serves both airports"""
    return (
        departure.upper() in sunexpress_destinations
        and arrival.upper() in sunexpress_destinations
    )


def get_route_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate simplified prompt for route compliance check"""
    return f"""
Check if SunExpress was available but a different airline was used.

Rule: {ROUTE_RULE}

Travel Approval: {json.dumps(travel_approval, indent=2)}
Flight Reservations: {json.dumps(flight_reservations, indent=2)}

Check each flight - if SunExpress serves both airports but traveler used different airline, it's a violation.
Set status to "NON_COMPLIANT" if any violations found, otherwise "COMPLIANT".
"""


class RouteAgent:
    def __init__(self, llm):
        self.llm = llm
        self.structured_llm = llm.with_structured_output(RouteComplianceResult)
        self.sunexpress_destinations = load_sunexpress_destinations()

    def check_route_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if traveler used alternative airlines when SunExpress was available"""

        violations = []

        for reservation in flight_reservations:
            flights = reservation.get("flights", [])
            # Use actual field names from Ticket.json (source of truth)
            booking_ref = reservation.get("confirmationNumber", "")

            for flight in flights:
                # Use actual field names from Ticket.json (source of truth)
                airline_code = flight.get("airlineCompanyCode", "")
                flight_number = flight.get("flightNo", "")
                departure_airport = flight.get("departureAirPortCode", "")
                arrival_airport = flight.get("arrivalAirPortCode", "")

                # Skip if already using SunExpress
                if airline_code == "XQ":
                    continue

                # Check if SunExpress serves this route
                if check_sunexpress_serves_route(
                    departure_airport, arrival_airport, self.sunexpress_destinations
                ):
                    violations.append(
                        RouteViolation(
                            flight_number=flight_number,
                            reason=f"SunExpress serves {departure_airport}→{arrival_airport} but {airline_code} was used instead",
                            actual_airline=airline_code,
                            route=f"{departure_airport}→{arrival_airport}",
                            booking_reference=booking_ref,
                        )
                    )

        # Determine status and message
        if violations:
            status = "NON_COMPLIANT"
            message = f"Found {len(violations)} route violations - SunExpress was available but not used"
        else:
            status = "COMPLIANT"
            message = "All flights comply with SunExpress route policy"

        return {
            "rule_name": "SunExpress Route Compliance",
            "status": status,
            "message": message,
            "violations": [v.model_dump() for v in violations],
        }
