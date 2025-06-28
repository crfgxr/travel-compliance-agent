from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Any
import json
import logging
import requests
import time
import os
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

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

TIMING_VIOLATION_TEMPLATE = {
    "flight_number": "flight number (e.g., XQ141)",
    "reason": "Clear explanation of why this violates the rule",
    "departure_date": "actual departure date/time",
    "arrival_date": "actual arrival date/time",
    "approved_period": "approved travel period dates",
    "issue_type": "departure_too_early|arrival_too_late|departure_too_late|arrival_too_early",
}


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

PASSENGER_IDENTITY_VIOLATION_TEMPLATE = {
    "passenger_name": "passenger name from ticket",
    "reason": "Clear explanation of why this passenger is not compliant",
    "ticket_employee_id": "employee ID from flight ticket",
    "approved_employee_id": "employee ID from travel approval (if exists)",
    "booking_reference": "booking ID or confirmation number",
    "issue_type": "name_mismatch|employee_id_mismatch|unauthorized_passenger|missing_approval",
    "expected_name": "correct name from approval (if applicable)",
}


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

ROUTE_COMPLIANCE_VIOLATION_TEMPLATE = {
    "flight_number": "flight number (e.g., TK123)",
    "reason": "Clear explanation of why this flight violates the SunExpress route policy",
    "actual_airline": "airline code that was used",
    "actual_airline_name": "full airline name that was used",
    "route": "departure airport -> arrival airport (e.g., IST -> FRA)",
    "travel_date": "date when travel occurred",
    "booking_reference": "booking ID or confirmation number",
    "sunexpress_availability": "confirmation that SunExpress serves both airports",
    "route_details": "details about SunExpress airport coverage",
    "policy_rule": "SunExpress route availability violation",
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
) -> Dict[str, Any]:
    """
    Analyze route compliance by checking SunExpress availability using airline route data

    Returns:
        Dict with compliance analysis results
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
                    {
                        "flight_number": flight_number,
                        "reason": f"SunExpress operates the route {departure_airport} -> {arrival_airport}, but {airline_name} ({airline_code}) was used instead. This violates the SunExpress route optimization policy.",
                        "actual_airline": airline_code,
                        "actual_airline_name": airline_name,
                        "route": f"{departure_airport} -> {arrival_airport}",
                        "travel_date": travel_date,
                        "booking_reference": booking_ref,
                        "sunexpress_availability": availability.get(
                            "route_explanation", "SunExpress operates this route"
                        ),
                        "route_details": route_detail_text
                        or f"SunExpress operates {departure_airport} -> {arrival_airport} route",
                        "policy_rule": "SunExpress route availability violation",
                    }
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

    result = {
        "rule_name": "SunExpress Route Compliance",
        "status": status,
        "message": message,
        "details": {"violations": violations},
    }

    # Add data error information if any
    if api_errors:
        result["details"]["data_errors"] = api_errors
        # Build note from actual data errors
        error_summary = []
        for error in api_errors:
            error_summary.append(
                f"{error['route']} on {error['date']}: {error['error']}"
            )

        result["details"]["note"] = (
            f"Route verification failed for {len(api_errors)} route(s): "
            + "; ".join(error_summary)
        )

    return result


# =============================================================================
# PROMPT GENERATION FUNCTIONS
# =============================================================================


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


def get_route_compliance_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate prompt for SunExpress route compliance check using airline route data"""

    rules_text = "\n".join(
        [f"{i+1}. {rule}" for i, rule in enumerate(ROUTE_COMPLIANCE_RULES)]
    )

    return f"""
Check if traveler used alternative airlines when SunExpress was available on the same route.

Travel Approval Data:
{travel_approval}

Flight Reservations Data:
{flight_reservations}

Rules to check:
{rules_text}

IMPORTANT: Use the analyze_route_compliance_with_api() function which will:
1. For each flight in the reservations, extract route (origin → destination)
2. Use airline route data from GitHub to check if SunExpress operates the specific route
3. If SunExpress operates the route but traveler used a different airline, flag as violation
4. Skip flights that are already SunExpress (no violation)

BUSINESS LOGIC:
- Only flag as violation if SunExpress actually operates the specific route
- The goal is cost optimization - if SunExpress was available on the route, it should have been used
- Different airlines are acceptable ONLY if SunExpress doesn't operate that specific route

Call the analyze_route_compliance_with_api() function with the provided data and return its result directly.
The function will return a JSON response with this EXACT structure:
{{
    "rule_name": "{ROUTE_COMPLIANCE_RULE_CONFIG['rule_name']}",
    "status": "COMPLIANT",
    "message": "Brief summary of findings for the user",
    "details": {{
        "violations": [
            {{
                "flight_number": "flight number (e.g., TK123)",
                "reason": "Clear explanation of why this flight violates the SunExpress route policy",
                "actual_airline": "airline code that was used",
                "actual_airline_name": "full airline name that was used",
                "route": "departure airport -> arrival airport (e.g., IST -> FRA)",
                "travel_date": "date when travel occurred",
                "booking_reference": "booking ID or confirmation number",
                "sunexpress_availability": "confirmation that SunExpress serves both airports",
                "route_details": "details about SunExpress airport coverage",
                "policy_rule": "SunExpress route availability violation"
            }}
        ]
    }}
}}

Important:
- Status will be "NON_COMPLIANT" if violations found, "COMPLIANT" if no violations
- Violations include details about SunExpress airport coverage
- Clear explanation of cost optimization opportunity missed
- Information about which airports SunExpress serves
- If compliant, return empty violations array
- MUST return valid JSON object (not array)
- ALWAYS include all required fields: rule_name, status, message, details
"""


# =============================================================================
# RULE METADATA
# =============================================================================

ALL_RULES = {
    "timing": {
        "config": TIMING_RULE_CONFIG,
        "rules": TIMING_RULES,
        "prompt_function": get_timing_compliance_prompt,
    },
    "passenger_identity": {
        "config": PASSENGER_IDENTITY_RULE_CONFIG,
        "rules": PASSENGER_IDENTITY_RULES,
        "prompt_function": get_passenger_identity_prompt,
    },
    "route_compliance": {
        "config": ROUTE_COMPLIANCE_RULE_CONFIG,
        "rules": ROUTE_COMPLIANCE_RULES,
        "prompt_function": get_route_compliance_prompt,
    },
}


def get_all_rule_names() -> List[str]:
    """Get list of all rule names"""
    return [rule_data["config"]["rule_name"] for rule_data in ALL_RULES.values()]


def add_new_rule_type(rule_key: str, config: Dict, rules: List[str], prompt_function):
    """
    Add a new rule type to the system

    Args:
        rule_key: Unique identifier for the rule type
        config: Rule configuration dictionary
        rules: List of rule descriptions
        prompt_function: Function that generates prompts for this rule type
    """
    ALL_RULES[rule_key] = {
        "config": config,
        "rules": rules,
        "prompt_function": prompt_function,
    }


class ComplianceAgent:
    def __init__(self, llm: ChatOpenAI):
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

    def check_route_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if traveler used alternative airlines when SunExpress was available on the route using airline route data"""

        try:
            # Use the route data-based function to check SunExpress route compliance
            result = analyze_route_compliance_with_api(
                travel_approval, flight_reservations
            )

            # Ensure required fields are present
            if not isinstance(result, dict):
                return {
                    "rule_name": "SunExpress Route Compliance",
                    "status": "SYSTEM_ERROR",
                    "message": "Route data function returned invalid format",
                    "details": {
                        "error_type": "invalid_format",
                        "raw_response": result,
                    },
                }

            # Ensure status field exists
            if "status" not in result:
                result["status"] = "SYSTEM_ERROR"
                result["message"] = "Missing status field in route data response"
                result["rule_name"] = "SunExpress Route Compliance"

            return result

        except Exception as e:
            logger.error(f"Error in SunExpress route compliance check: {str(e)}")
            return {
                "rule_name": "SunExpress Route Compliance",
                "status": "SYSTEM_ERROR",
                "message": f"Error checking SunExpress route compliance: {str(e)}",
                "details": {
                    "error_type": "data_error",
                    "error_message": str(e),
                },
            }

    def generate_compliance_report(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
        progress_callback=None,
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report with progress tracking"""

        # Define the compliance checks to run
        compliance_checks = [
            {
                "name": "Flight Ticket Timing",
                "description": "Checking if flight times are within approved travel period",
                "method": self.check_timing_compliance,
                "icon": "⏰",
            },
            {
                "name": "Passenger Identity",
                "description": "Verifying passenger identities match approval records",
                "method": self.check_passenger_identity,
                "icon": "👤",
            },
            {
                "name": "SunExpress Route Compliance",
                "description": "Checking if SunExpress operates routes but alternative airlines were used",
                "method": self.check_route_compliance,
                "icon": "✈️",
            },
        ]

        results = []
        total_checks = len(compliance_checks)

        for i, check in enumerate(compliance_checks):
            # Update progress if callback provided
            if progress_callback:
                progress_callback(
                    current=i + 1,
                    total=total_checks,
                    current_job=check["name"],
                    description=check["description"],
                    icon=check["icon"],
                )

            # Log the current job
            logger.info(
                f"{check['icon']} Running {check['name']} check ({i+1}/{total_checks})"
            )

            # Execute the compliance check
            result = check["method"](travel_approval, flight_reservations)
            results.append(result)

            # Log completion
            status = result.get("status", "UNKNOWN")
            logger.info(f"✅ {check['name']} check completed: {status}")

        # Determine overall status
        # Define all error types that should be considered as system errors
        system_error_statuses = ["SYSTEM_ERROR", "json_parse_error", "llm_call_error"]

        system_error_count = sum(
            1
            for r in results
            if isinstance(r, dict) and r.get("status") in system_error_statuses
        )
        non_compliant_count = sum(
            1
            for r in results
            if isinstance(r, dict) and r.get("status") == "NON_COMPLIANT"
        )
        warning_count = sum(
            1 for r in results if isinstance(r, dict) and r.get("status") == "WARNING"
        )

        if system_error_count > 0:
            overall_status = "SYSTEM_ERROR"
            summary = f"SYSTEM ERROR: {system_error_count} system errors occurred"
        elif non_compliant_count > 0:
            overall_status = "NON_COMPLIANT"
            summary = f"VIOLATION: {non_compliant_count} critical violations found"
        elif warning_count > 0:
            overall_status = "WARNING"
            summary = f"WARNING: {warning_count} issues require attention"
        else:
            overall_status = "COMPLIANT"
            summary = "PASSED: All compliance rules satisfied"

        return {
            "overall_status": overall_status,
            "results": results,
            "summary": summary,
        }


# DONT CHANGE MODEL AND OUTPUT VERSION ITS WORKING
def create_llm_client(
    model: str,
    temperature: float = 0,
    openai_api_key: str = None,
) -> ChatOpenAI:
    """Create and return a ChatOpenAI instance"""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=openai_api_key,
        # output_version="responses/v1",  # Temporarily disabled
    )


# For backward compatibility, create an alias
OpenAIResponsesClient = create_llm_client

# v0.1 working
