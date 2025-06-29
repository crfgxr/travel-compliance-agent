from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import json
import logging

from .timing_agent import TimingAgent
from .identity_agent import IdentityAgent
from .route_agent import RouteAgent

# Setup logger
logger = logging.getLogger(__name__)


# =============================================================================
# RULE METADATA SYSTEM (moved from shared_utils)
# =============================================================================

ALL_RULES = {}


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


# =============================================================================
# COMPLIANCE ORCHESTRATOR
# =============================================================================


class ComplianceAgent:
    def __init__(self, model: str, temperature: float = 0, openai_api_key: str = None):
        # Create LLM instance with model provided from UI
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=openai_api_key,
        )

        # Initialize individual agents with the shared LLM instance
        self.timing_agent = TimingAgent(self.llm)
        self.identity_agent = IdentityAgent(self.llm)
        self.route_agent = RouteAgent(self.llm)

    def check_timing_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if flight times fall within travel approval dates using LLM"""
        return self.timing_agent.check_timing_compliance(
            travel_approval, flight_reservations
        )

    def check_passenger_identity(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check passenger name consistency between approval and reservations using LLM"""
        return self.identity_agent.check_passenger_identity(
            travel_approval, flight_reservations
        )

    def check_route_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if traveler used alternative airlines when SunExpress was available on the route using airline route data"""
        return self.route_agent.check_route_compliance(
            travel_approval, flight_reservations
        )

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
