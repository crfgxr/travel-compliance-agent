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
    IDENTITY_RULE,
    get_identity_prompt,
)
from .route_agent import (
    RouteAgent,
    ROUTE_RULE,
    load_sunexpress_destinations,
    check_sunexpress_serves_route,
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
    "IDENTITY_RULE",
    "get_identity_prompt",
    # Route compliance
    "ROUTE_RULE",
    "load_sunexpress_destinations",
    "check_sunexpress_serves_route",
]
