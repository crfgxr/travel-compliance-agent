# Backward compatibility - expose the main class
from .orchestrator import ComplianceAgent


# Also expose individual agents if needed
from .timing_agent import (
    TimingAgent,
    TIMING_RULE,
    get_timing_prompt,
)
from .identity_agent import (
    IdentityAgent,
    PASSENGER_IDENTITY_RULES,
    PASSENGER_IDENTITY_RULE_CONFIG,
    get_passenger_identity_prompt,
)
from .route_agent import (
    RouteAgent,
    ROUTE_COMPLIANCE_RULES,
    ROUTE_COMPLIANCE_RULE_CONFIG,
    fetch_airline_route_data,
    check_sunexpress_route_availability,
    analyze_route_compliance_with_api,
)

__all__ = [
    # Main classes
    "ComplianceAgent",
    "TimingAgent",
    "IdentityAgent",
    "RouteAgent",
    # Timing compliance
    "TIMING_RULE",
    "get_timing_prompt",
    # Identity compliance
    "PASSENGER_IDENTITY_RULES",
    "PASSENGER_IDENTITY_RULE_CONFIG",
    "get_passenger_identity_prompt",
    # Route compliance
    "ROUTE_COMPLIANCE_RULES",
    "ROUTE_COMPLIANCE_RULE_CONFIG",
    "fetch_airline_route_data",
    "check_sunexpress_route_availability",
    "analyze_route_compliance_with_api",
]
