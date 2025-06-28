from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Any
import json
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

        try:
            response = self.llm.invoke([system_message, human_message])
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError as e:
            return {
                "rule_name": TIMING_RULE_CONFIG["rule_name"],
                "status": "NON_COMPLIANT",
                "message": "Failed to parse AI response as valid JSON",
                "details": {
                    "error_type": "json_parse_error",
                    "error_message": str(e),
                    "raw_response": (
                        response.content
                        if "response" in locals()
                        else "No response received"
                    ),
                    "violations": [],
                },
            }
        except Exception as e:
            return {
                "rule_name": TIMING_RULE_CONFIG["rule_name"],
                "status": "SYSTEM_ERROR",
                "message": "System error occurred during compliance analysis",
                "details": {
                    "error_type": "system_error",
                    "error_message": str(e),
                    "violations": [{"error": "Analysis failed"}],
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

        try:
            response = self.llm.invoke([system_message, human_message])
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError as e:
            return {
                "rule_name": PASSENGER_IDENTITY_RULE_CONFIG["rule_name"],
                "status": "NON_COMPLIANT",
                "message": "Failed to parse AI response as valid JSON",
                "details": {
                    "error_type": "json_parse_error",
                    "error_message": str(e),
                    "raw_response": (
                        response.content
                        if "response" in locals()
                        else "No response received"
                    ),
                    "violations": [],
                },
            }
        except Exception as e:
            return {
                "rule_name": PASSENGER_IDENTITY_RULE_CONFIG["rule_name"],
                "status": "SYSTEM_ERROR",
                "message": "System error occurred during compliance analysis",
                "details": {
                    "error_type": "system_error",
                    "error_message": str(e),
                    "violations": [{"error": "Analysis failed"}],
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

        try:
            response = self.llm.invoke([system_message, human_message])
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError as e:
            return {
                "rule_name": ROUTE_COMPLIANCE_RULE_CONFIG["rule_name"],
                "status": "NON_COMPLIANT",
                "message": "Failed to parse AI response as valid JSON",
                "details": {
                    "error_type": "json_parse_error",
                    "error_message": str(e),
                    "raw_response": (
                        response.content
                        if "response" in locals()
                        else "No response received"
                    ),
                    "violations": [],
                },
            }
        except Exception as e:
            return {
                "rule_name": ROUTE_COMPLIANCE_RULE_CONFIG["rule_name"],
                "status": "SYSTEM_ERROR",
                "message": "System error occurred during compliance analysis",
                "details": {
                    "error_type": "system_error",
                    "error_message": str(e),
                    "violations": [{"error": "Analysis failed"}],
                },
            }

    def generate_compliance_report(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""

        results = [
            self.check_timing_compliance(travel_approval, flight_reservations),
            self.check_passenger_identity(travel_approval, flight_reservations),
            self.check_route_compliance(travel_approval, flight_reservations),
        ]

        # Determine overall status
        system_error_count = sum(
            1 for r in results if r.get("status") == "SYSTEM_ERROR"
        )
        non_compliant_count = sum(
            1 for r in results if r.get("status") == "NON_COMPLIANT"
        )
        warning_count = sum(1 for r in results if r.get("status") == "WARNING")

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
    """Create and return a ChatOpenAI instance with Responses API"""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=openai_api_key,
        output_version="responses/v1",  # Enable Responses API
    )


# For backward compatibility, create an alias
OpenAIResponsesClient = create_llm_client
