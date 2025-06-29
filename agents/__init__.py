# Backward compatibility - expose the main class
from .orchestrator import ComplianceAgent
from .shared_utils import (
    create_llm_client,
    OpenAIResponsesClient,
    ALL_RULES,
    get_all_rule_names,
    add_new_rule_type,
)

# Also expose individual agents if needed
from .timing_agent import (
    TimingAgent,
    TIMING_RULES,
    TIMING_RULE_CONFIG,
    get_timing_compliance_prompt,
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
    get_route_compliance_prompt,
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
    # LLM client utilities
    "create_llm_client",
    "OpenAIResponsesClient",
    # Rule management
    "ALL_RULES",
    "get_all_rule_names",
    "add_new_rule_type",
    # Timing compliance
    "TIMING_RULES",
    "TIMING_RULE_CONFIG",
    "get_timing_compliance_prompt",
    # Identity compliance
    "PASSENGER_IDENTITY_RULES",
    "PASSENGER_IDENTITY_RULE_CONFIG",
    "get_passenger_identity_prompt",
    # Route compliance
    "ROUTE_COMPLIANCE_RULES",
    "ROUTE_COMPLIANCE_RULE_CONFIG",
    "get_route_compliance_prompt",
    "fetch_airline_route_data",
    "check_sunexpress_route_availability",
    "analyze_route_compliance_with_api",
]


# Initialize the ALL_RULES dictionary with all rule types for backward compatibility
from .shared_utils import add_new_rule_type
from .timing_agent import TIMING_RULES, TIMING_RULE_CONFIG, get_timing_compliance_prompt
from .identity_agent import (
    PASSENGER_IDENTITY_RULES,
    PASSENGER_IDENTITY_RULE_CONFIG,
    get_passenger_identity_prompt,
)
from .route_agent import (
    ROUTE_COMPLIANCE_RULES,
    ROUTE_COMPLIANCE_RULE_CONFIG,
    get_route_compliance_prompt,
)

# Populate ALL_RULES for backward compatibility
add_new_rule_type(
    "timing", TIMING_RULE_CONFIG, TIMING_RULES, get_timing_compliance_prompt
)

add_new_rule_type(
    "passenger_identity",
    PASSENGER_IDENTITY_RULE_CONFIG,
    PASSENGER_IDENTITY_RULES,
    get_passenger_identity_prompt,
)

add_new_rule_type(
    "route_compliance",
    ROUTE_COMPLIANCE_RULE_CONFIG,
    ROUTE_COMPLIANCE_RULES,
    get_route_compliance_prompt,
)
