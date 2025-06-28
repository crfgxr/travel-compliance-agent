from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Any
import json
import logging

# Setup logger
logger = logging.getLogger(__name__)
from rules import (
    get_timing_compliance_prompt,
    get_passenger_identity_prompt,
    get_route_compliance_prompt,
    TIMING_RULE_CONFIG,
    PASSENGER_IDENTITY_RULE_CONFIG,
    ROUTE_COMPLIANCE_RULE_CONFIG,
)


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
        """Check if different airlines are used on SunExpress account routes using LLM"""

        system_message = SystemMessage(
            content="You are a travel compliance expert. Analyze airline route compliance and provide assessments in JSON format."
        )

        # Generate prompt using centralized rules
        user_prompt = get_route_compliance_prompt(
            json.dumps(travel_approval, indent=2),
            json.dumps(flight_reservations, indent=2),
        )

        human_message = HumanMessage(content=user_prompt)

        # First, try to call the LLM
        try:
            response = self.llm.invoke([system_message, human_message])
        except Exception as e:
            return {
                "rule_name": "Route Compliance",
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
                    "rule_name": "Route Compliance",
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
                result["rule_name"] = "Route Compliance"

            return result
        except (json.JSONDecodeError, TypeError) as e:
            return {
                "rule_name": "Route Compliance",
                "status": "json_parse_error",
                "message": "Failed to parse LLM response as valid JSON",
                "details": {
                    "error_type": "json_parse_error",
                    "error_message": str(e),
                    "raw_response": response.content,
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
                "name": "Route Compliance",
                "description": "Validating airline usage follows account policies",
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
        system_error_count = sum(
            1
            for r in results
            if isinstance(r, dict) and r.get("status") == "SYSTEM_ERROR"
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
            summary = f"FAILED: {non_compliant_count} critical violations found"
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
