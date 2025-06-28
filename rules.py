"""
Travel Compliance Rules Configuration

This file contains all compliance rules used by the Travel Compliance Agent.
Rules can be easily added, modified, or removed by updating the appropriate sections.
"""

from typing import Dict, Any, List


# =============================================================================
# TIMING COMPLIANCE RULES
# =============================================================================

TIMING_RULES = [
    "All flight departures must be within the travel period (travelBeginDate to travelEndDate)",
    "All flight arrivals must be within the travel period (travelBeginDate to travelEndDate)",
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
    "recommendation": "What needs to be done to resolve this issue",
}


# =============================================================================
# ROUTE COMPLIANCE RULES
# =============================================================================

ROUTE_COMPLIANCE_RULES = [
    'If accountName is "SunExpress", all flights must use SunExpress airline (code "XQ")',
    "Other accounts can use any airline",
]

ROUTE_COMPLIANCE_RULE_CONFIG = {
    "rule_name": "Route Compliance",
    "description": "Check if airline usage follows account-specific rules",
    "account_rules": {
        "SunExpress": {
            "required_airline_code": "XQ",
            "required_airline_name": "SunExpress",
        }
        # Add more account-specific rules here as needed
    },
}

ROUTE_COMPLIANCE_VIOLATION_TEMPLATE = {
    "flight_number": "flight number (e.g., TK123)",
    "reason": "Clear explanation of why this flight violates the airline policy",
    "actual_airline": "airline code that was used",
    "actual_airline_name": "full airline name",
    "required_airline": "airline code that should have been used",
    "required_airline_name": "full name of required airline",
    "account_name": "travel account name",
    "route": "departure airport -> arrival airport",
    "booking_reference": "booking ID or confirmation number",
    "policy_rule": "specific policy rule that was violated",
    "recommendation": "What action should be taken to resolve this",
}


# =============================================================================
# PROMPT GENERATION FUNCTIONS
# =============================================================================


def get_timing_compliance_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate prompt for timing compliance check"""

    rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(TIMING_RULES)])

    return f"""
Check if flight times fall within the approved travel period.

Travel Approval Data:
{travel_approval}

Flight Reservations Data:
{flight_reservations}

Rules to check:
{rules_text}

Analyze the data and return a JSON response with:
{{
    "rule_name": "{TIMING_RULE_CONFIG['rule_name']}",
    "status": "COMPLIANT" or "NON_COMPLIANT",
    "message": "Brief summary of findings for the user",
    "details": {{
        "violations": [
            {TIMING_VIOLATION_TEMPLATE}
        ]
    }}
}}

Important: 
- Write violation reasons in clear, user-friendly language
- Explain exactly what rule was broken and why
- Provide actionable recommendations
- If compliant, return empty violations array
- Only return valid JSON
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

Analyze the data and return a JSON response with:
{{
    "rule_name": "{PASSENGER_IDENTITY_RULE_CONFIG['rule_name']}",
    "status": "COMPLIANT" or "NON_COMPLIANT",
    "message": "Brief summary of findings for the user",
    "details": {{
        "violations": [
            {PASSENGER_IDENTITY_VIOLATION_TEMPLATE}
        ]
    }}
}}

Important:
- Write violation reasons in clear, user-friendly language
- Explain exactly what identity issue was found
- Show what was expected vs what was found
- Provide specific steps to resolve each issue
- If compliant, return empty violations array
- Only return valid JSON
"""


def get_route_compliance_prompt(
    travel_approval: Dict[str, Any], flight_reservations: List[Dict[str, Any]]
) -> str:
    """Generate prompt for route compliance check"""

    rules_text = "\n".join(
        [f"{i+1}. {rule}" for i, rule in enumerate(ROUTE_COMPLIANCE_RULES)]
    )

    return f"""
Check if airline usage follows account-specific rules.

Travel Approval Data:
{travel_approval}

Flight Reservations Data:
{flight_reservations}

Rules to check:
{rules_text}

Analyze the data and return a JSON response with:
{{
    "rule_name": "{ROUTE_COMPLIANCE_RULE_CONFIG['rule_name']}",
    "status": "COMPLIANT" or "NON_COMPLIANT", 
    "message": "Brief summary of findings for the user",
    "details": {{
        "violations": [
            {ROUTE_COMPLIANCE_VIOLATION_TEMPLATE}
        ]
    }}
}}

Important:
- Write violation reasons in clear, user-friendly language
- Explain which airline policy rule was broken
- Show what airline was used vs what should have been used
- Include full airline names, not just codes
- Provide clear instructions on how to fix the issue
- If compliant, return empty violations array
- Only return valid JSON
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
