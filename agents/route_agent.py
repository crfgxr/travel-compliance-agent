from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import logging
import requests
import time
import os

# Setup logger
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================


class RouteViolation(BaseModel):
    """Model for route compliance violations"""

    flight_number: str = Field(description="Flight number (e.g., TK123)")
    reason: str = Field(
        description="Clear explanation of why this flight violates the SunExpress route policy"
    )
    actual_airline: str = Field(description="Airline code that was used")
    actual_airline_name: str = Field(description="Full airline name that was used")
    route: str = Field(
        description="Departure airport -> arrival airport (e.g., IST -> FRA)"
    )
    travel_date: str = Field(description="Date when travel occurred")
    booking_reference: str = Field(description="Booking ID or confirmation number")
    sunexpress_availability: str = Field(
        description="Confirmation that SunExpress serves both airports"
    )
    route_details: str = Field(description="Details about SunExpress airport coverage")
    policy_rule: str = Field(
        default="SunExpress route availability violation",
        description="Policy rule violated",
    )


class RouteDetails(BaseModel):
    """Model for route compliance details"""

    violations: List[RouteViolation] = Field(
        default=[], description="List of route violations found"
    )
    data_errors: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Any data retrieval errors"
    )
    note: Optional[str] = Field(
        default=None, description="Additional notes about data issues"
    )


class RouteComplianceResult(BaseModel):
    """Model for route compliance check result"""

    rule_name: str = Field(
        default="SunExpress Route Compliance", description="Name of the compliance rule"
    )
    status: str = Field(
        description="Compliance status: COMPLIANT, NON_COMPLIANT, or UNKNOWN"
    )
    message: str = Field(description="Brief summary of findings for the user")
    details: RouteDetails = Field(description="Detailed violation information")


# =============================================================================
# ROUTE COMPLIANCE RULES
# =============================================================================

ROUTE_COMPLIANCE_RULES = [
    "Check if SunExpress (airline code 'XQ') serves the specific route between departure and arrival airports",
    "If SunExpress serves the route but traveler used a different airline, this is a violation",
    "Use airline route data to verify SunExpress route availability",
    "Only flag as violation if SunExpress actually operates the specific route",
]

ROUTE_COMPLIANCE_RULE_CONFIG = {
    "rule_name": "SunExpress Route Compliance",
    "description": "Check if traveler used alternative airlines when SunExpress was available on the route",
    "sunexpress_airline_code": "XQ",
    "sunexpress_airline_name": "SunExpress",
    "route_data_source": "https://raw.githubusercontent.com/Jonty/airline-route-data/refs/heads/main/airline_routes.json",
}


# =============================================================================
# AIRLINE ROUTE DATA INTEGRATION
# =============================================================================


def fetch_airline_route_data(cache_timeout: int = 3600) -> Dict[str, Any]:
    """
    Fetch airline route data from GitHub repository

    Returns:
        Dict with airline route data or error information
    """
    # Simple caching mechanism
    cache_file = "/tmp/airline_routes_cache.json"

    # Check if cache exists and is still valid
    if os.path.exists(cache_file):
        try:
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < cache_timeout:
                with open(cache_file, "r") as f:
                    return json.load(f)
        except:
            pass  # If cache read fails, continue to fetch fresh data

    try:
        url = "https://raw.githubusercontent.com/Jonty/airline-route-data/refs/heads/main/airline_routes.json"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Cache the data
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except:
            pass  # If cache write fails, continue with the data

        return data
    except requests.RequestException as e:
        return {
            "error": f"Failed to fetch airline route data: {str(e)}",
            "api_success": False,
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse airline route data: {str(e)}",
            "api_success": False,
        }


def check_sunexpress_route_availability(
    origin_airport: str,
    destination_airport: str,
    travel_date: str,
) -> Dict[str, Any]:
    """
    Check if SunExpress serves a route between two airports using airline route data

    Args:
        origin_airport: IATA code for departure airport (e.g., 'IST')
        destination_airport: IATA code for arrival airport (e.g., 'FRA')
        travel_date: Date in YYYY-MM-DD format (for compatibility, not used in this implementation)

    Returns:
        Dict with availability info based on route data
    """

    # Fetch airline route data
    route_data = fetch_airline_route_data()

    if "error" in route_data:
        return {
            "sunexpress_available": False,
            "route": f"{origin_airport} -> {destination_airport}",
            "travel_date": travel_date,
            "origin_served": False,
            "destination_served": False,
            "api_success": False,
            "api_error": route_data["error"],
        }

    try:
        origin_upper = origin_airport.upper()
        destination_upper = destination_airport.upper()

        # Check if origin airport exists in the data
        if origin_upper not in route_data:
            return {
                "sunexpress_available": False,
                "route": f"{origin_airport} -> {destination_airport}",
                "travel_date": travel_date,
                "origin_served": False,
                "destination_served": False,
                "route_explanation": f"Origin airport {origin_airport} not found in route data",
                "api_success": True,
            }

        # Get routes from origin airport
        origin_routes = route_data[origin_upper].get("routes", [])

        # Check if there's a route to the destination airport served by SunExpress
        sunexpress_available = False
        route_details = []

        for route in origin_routes:
            if route.get("iata") == destination_upper:
                # Found a route to destination, check if SunExpress serves it
                carriers = route.get("carriers", [])
                for carrier in carriers:
                    if carrier.get("iata") == "XQ":  # SunExpress IATA code
                        sunexpress_available = True
                        route_details.append(
                            {
                                "distance_km": route.get("km", 0),
                                "flight_time_min": route.get("min", 0),
                                "carrier_name": carrier.get("name", "SunExpress"),
                            }
                        )
                        break
                break

        # Also check reverse route (destination -> origin) for completeness
        destination_served = False
        if destination_upper in route_data:
            destination_routes = route_data[destination_upper].get("routes", [])
            for route in destination_routes:
                if route.get("iata") == origin_upper:
                    carriers = route.get("carriers", [])
                    for carrier in carriers:
                        if carrier.get("iata") == "XQ":
                            destination_served = True
                            break
                    break

        return {
            "sunexpress_available": sunexpress_available,
            "route": f"{origin_airport} -> {destination_airport}",
            "travel_date": travel_date,
            "origin_served": sunexpress_available,
            "destination_served": destination_served,
            "route_explanation": f"SunExpress serves {origin_airport} -> {destination_airport}: {sunexpress_available}",
            "route_details": route_details,
            "api_success": True,
        }

    except Exception as e:
        return {
            "sunexpress_available": False,
            "route": f"{origin_airport} -> {destination_airport}",
            "travel_date": travel_date,
            "origin_served": False,
            "destination_served": False,
            "api_success": False,
            "api_error": f"Error processing route data: {str(e)}",
        }


def analyze_route_compliance_with_api(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> RouteComplianceResult:
    """
    Analyze route compliance by checking SunExpress availability using airline route data
    Now returns a Pydantic model for consistency

    Returns:
        RouteComplianceResult with compliance analysis results
    """
    violations = []
    api_errors = []

    for reservation in flight_reservations:
        # Extract flight details
        flights = reservation.get("flights", [])
        booking_ref = reservation.get("bookingReference", "")

        for flight in flights:
            # Handle different field name variations from sample data
            airline_code = flight.get("airlineCode", "") or flight.get(
                "airlineCompanyCode", ""
            )
            airline_name = flight.get("airlineName", "") or flight.get(
                "airlineCompanyName", ""
            )
            flight_number = flight.get("flightNumber", "") or flight.get("flightNo", "")
            departure_airport = flight.get("departureAirport", "") or flight.get(
                "departureAirPortCode", ""
            )
            arrival_airport = flight.get("arrivalAirport", "") or flight.get(
                "arrivalAirPortCode", ""
            )
            departure_date = flight.get("departureDate", "")

            # Skip if this is already a SunExpress flight
            if airline_code == "XQ":
                continue

            # Extract date from departure datetime
            travel_date = (
                departure_date.split("T")[0]
                if "T" in departure_date
                else departure_date.split()[0]
            )

            # Check if SunExpress operates on this route
            availability = check_sunexpress_route_availability(
                departure_airport, arrival_airport, travel_date
            )

            # Check for API errors
            if not availability.get("api_success", False):
                api_errors.append(
                    {
                        "route": f"{departure_airport} -> {arrival_airport}",
                        "date": travel_date,
                        "error": availability.get("api_error", "Unknown API error"),
                    }
                )
                continue  # Skip this flight due to API error

            # If SunExpress was available but traveler used different airline
            if availability["sunexpress_available"]:
                route_info = availability.get("route_details", [])
                route_detail_text = ""
                if route_info:
                    detail = route_info[0]  # Get first route detail
                    route_detail_text = f"Distance: {detail.get('distance_km', 0)}km, Flight time: {detail.get('flight_time_min', 0)} minutes"

                violations.append(
                    RouteViolation(
                        flight_number=flight_number,
                        reason=f"SunExpress operates the route {departure_airport} -> {arrival_airport}, but {airline_name} ({airline_code}) was used instead. This violates the SunExpress route optimization policy.",
                        actual_airline=airline_code,
                        actual_airline_name=airline_name,
                        route=f"{departure_airport} -> {arrival_airport}",
                        travel_date=travel_date,
                        booking_reference=booking_ref,
                        sunexpress_availability=availability.get(
                            "route_explanation", "SunExpress operates this route"
                        ),
                        route_details=route_detail_text
                        or f"SunExpress operates {departure_airport} -> {arrival_airport} route",
                        policy_rule="SunExpress route availability violation",
                    )
                )

    # Determine final status and message
    if api_errors:
        if violations:
            status = "NON_COMPLIANT"
            message = f"Found {len(violations)} SunExpress route compliance violation(s). Note: {len(api_errors)} route(s) could not be checked due to data issues."
        else:
            status = "UNKNOWN"
            message = f"Could not complete route compliance check due to data issues on {len(api_errors)} route(s)."
    else:
        status = "NON_COMPLIANT" if violations else "COMPLIANT"
        message = (
            f"Found {len(violations)} SunExpress route compliance violation(s)"
            if violations
            else "All flights comply with SunExpress route policy"
        )

    # Create the details object
    details = RouteDetails(violations=violations)

    # Add data error information if any
    if api_errors:
        details.data_errors = api_errors
        # Build note from actual data errors
        error_summary = []
        for error in api_errors:
            error_summary.append(
                f"{error['route']} on {error['date']}: {error['error']}"
            )

        details.note = (
            f"Route verification failed for {len(api_errors)} route(s): "
            + "; ".join(error_summary)
        )

    return RouteComplianceResult(
        rule_name="SunExpress Route Compliance",
        status=status,
        message=message,
        details=details,
    )


class RouteAgent:
    def __init__(self, llm):
        self.llm = llm
        # Create structured output LLM (for potential future LLM-based route checking)
        self.structured_llm = llm.with_structured_output(RouteComplianceResult)

    def check_route_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if traveler used alternative airlines when SunExpress was available on the route using airline route data with structured output"""

        try:
            # Use the route data-based function to check SunExpress route compliance
            result = analyze_route_compliance_with_api(
                travel_approval, flight_reservations
            )

            # Convert Pydantic model to dictionary for compatibility with existing code
            return result.model_dump()

        except Exception as e:
            logger.error(f"Error in SunExpress route compliance check: {str(e)}")
            return {
                "rule_name": "SunExpress Route Compliance",
                "status": "SYSTEM_ERROR",
                "message": f"System error during route compliance check: {str(e)}",
                "details": {
                    "violations": [],
                    "error_type": "data_error",
                    "error_message": str(e),
                },
            }
