from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
from typing import List, Dict, Any
import json
from datetime import datetime


class SchemaValidationAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def validate_schema(self, data: dict, schema_type: str) -> Dict[str, Any]:
        """Validate JSON schema using AI"""
        prompt = f"""
        You are a schema validation expert. Validate if the provided JSON data follows the expected schema for {schema_type}.
        
        Data to validate: {json.dumps(data, indent=2)}
        
        Check for:
        1. Required fields presence
        2. Data types correctness
        3. Date format validity
        4. Logical consistency
        
        Return your response as JSON with:
        - "valid": boolean
        - "errors": list of error messages
        - "warnings": list of warning messages
        """

        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.content)
        except:
            return {"valid": False, "errors": ["Failed to parse validation response"]}


class ComplianceAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def check_timing_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if flight times fall within travel approval dates using LLM"""

        prompt = f"""
        You are a travel compliance expert. Check if flight times fall within the approved travel period.
        
        Travel Approval Data:
        {json.dumps(travel_approval, indent=2)}
        
        Flight Reservations Data:
        {json.dumps(flight_reservations, indent=2)}
        
        Rules to check:
        1. All flight departures must be within the travel period (travelBeginDate to travelEndDate)
        2. All flight arrivals must be within the travel period (travelBeginDate to travelEndDate)
        
        Analyze the data and return a JSON response with:
        {{
            "rule_name": "Flight Ticket Timing",
            "status": "COMPLIANT" or "NON_COMPLIANT",
            "message": "Brief summary of findings",
            "details": {{
                "violations": [
                    {{
                        "flight": "flight number",
                        "issue": "description of issue",
                        "departure": "departure date/time",
                        "arrival": "arrival date/time", 
                        "travel_period": "approved travel period"
                    }}
                ]
            }}
        }}
        
        If compliant, return empty violations array.
        """

        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.content)
        except:
            return {
                "rule_name": "Flight Ticket Timing",
                "status": "NON_COMPLIANT",
                "message": "Failed to analyze timing compliance",
                "details": {"violations": [{"error": "Analysis failed"}]},
            }

    def check_passenger_identity(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check passenger name consistency between approval and reservations using LLM"""

        prompt = f"""
        You are a travel compliance expert. Check if passenger identities match between travel approval and flight reservations.
        
        Travel Approval Data:
        {json.dumps(travel_approval, indent=2)}
        
        Flight Reservations Data:
        {json.dumps(flight_reservations, indent=2)}
        
        Rules to check:
        1. All passengers in flight reservations must be in the approved passenger list
        2. Employee IDs must match between approval and reservations
        3. Names must match exactly (case-insensitive comparison)
        
        Analyze the data and return a JSON response with:
        {{
            "rule_name": "Passenger Identity",
            "status": "COMPLIANT" or "NON_COMPLIANT",
            "message": "Brief summary of findings",
            "details": {{
                "violations": [
                    {{
                        "passenger": "passenger name",
                        "issue": "description of issue",
                        "employee_id": "employee ID from ticket",
                        "booking_id": "booking reference",
                        "approved_employee_id": "employee ID from approval (if different)"
                    }}
                ]
            }}
        }}
        
        If compliant, return empty violations array.
        """

        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.content)
        except:
            return {
                "rule_name": "Passenger Identity",
                "status": "NON_COMPLIANT",
                "message": "Failed to analyze passenger identity compliance",
                "details": {"violations": [{"error": "Analysis failed"}]},
            }

    def check_route_compliance(
        self,
        travel_approval: Dict[str, Any],
        flight_reservations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if different airlines are used on SunExpress account routes using LLM"""

        prompt = f"""
        You are a travel compliance expert. Check if airline usage follows account-specific rules.
        
        Travel Approval Data:
        {json.dumps(travel_approval, indent=2)}
        
        Flight Reservations Data:
        {json.dumps(flight_reservations, indent=2)}
        
        Rules to check:
        1. If accountName is "SunExpress", all flights must use SunExpress airline (code "XQ")
        2. Other accounts can use any airline
        
        Analyze the data and return a JSON response with:
        {{
            "rule_name": "Route Compliance",
            "status": "COMPLIANT" or "NON_COMPLIANT", 
            "message": "Brief summary of findings",
            "details": {{
                "violations": [
                    {{
                        "flight": "flight number",
                        "airline": "airline code used",
                        "route": "departure -> arrival",
                        "booking_id": "booking reference",
                        "issue": "description of violation"
                    }}
                ]
            }}
        }}
        
        If compliant, return empty violations array.
        """

        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.content)
        except:
            return {
                "rule_name": "Route Compliance",
                "status": "NON_COMPLIANT",
                "message": "Failed to analyze route compliance",
                "details": {"violations": [{"error": "Analysis failed"}]},
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
        non_compliant_count = sum(
            1 for r in results if r.get("status") == "NON_COMPLIANT"
        )
        warning_count = sum(1 for r in results if r.get("status") == "WARNING")

        if non_compliant_count > 0:
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


class ChatAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def answer_question(self, question: str, context: dict) -> str:
        """Answer questions about travel compliance using context"""

        prompt = f"""
        You are a travel compliance expert. Answer the user's question based on the provided context.
        
        Context: {json.dumps(context, indent=2, default=str)}
        
        Question: {question}
        
        Provide a clear, helpful answer focusing on travel compliance rules and the specific data provided.
        """

        response = self.llm.invoke(prompt)
        return response.content
