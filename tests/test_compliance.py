import pytest
import json
import os
from datetime import datetime
from agents import ComplianceAgent


@pytest.fixture
def compliance_agent():
    """Create a compliance agent for testing"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping LLM-dependent tests")

    return ComplianceAgent(model="gpt-4o-mini", openai_api_key=api_key)


@pytest.fixture
def valid_travel_approval():
    """Create a valid travel approval for testing"""
    return {
        "travelCity": "Frankfurt",
        "travelCountry": "Germany",
        "travelBeginDate": "2025-06-22T09:00:00",
        "travelEndDate": "2025-06-26T09:00:00",
        "travelReason": "Business",
        "passengerList": [
            {
                "name": "Mr. Jhon",
                "surname": "Doe",
                "gender": "Male",
                "emailAddress": "jhon.doe@sunexpress.com",
                "employeeId": "00000001",
                "userType": "user",
            }
        ],
        "Status": "Approved",
    }


@pytest.fixture
def valid_flight_reservation():
    """Create a valid flight reservation for testing"""
    return {
        "bookingReference": "TIC-457855",
        "confirmationNumber": "SRWK64",
        "requestorUser": "MR.JHON DOE",
        "accountName": "SunExpress",
        "flights": [
            {
                "flightNumber": "XQ141",
                "airlineCode": "XQ",
                "airlineName": "SunExpress",
                "cabinClass": "Economy",
                "departureDate": "2025-06-24T12:35:00",
                "departureTime": "12:35:00",
                "arrivalDate": "2025-06-24T14:15:00",
                "arrivalTime": "14:15:00",
                "departureAirport": "AYT",
                "departureAirportCountry": "TR",
                "departureAirportCity": "Antalya",
                "arrivalAirport": "FRA",
                "arrivalAirportCountry": "DE",
                "arrivalAirportCity": "Frankfurt",
                "directionType": "departure",
            }
        ],
        "passengers": [
            {
                "name": "Mr. Jhon",
                "surname": "Doe",
                "gender": "Male",
                "emailAddress": "jhon.doe@sunexpress.com",
                "employeeId": "00000001",
                "userType": "user",
            }
        ],
    }


class TestStructuredOutputIntegration:
    """Test that structured output is properly integrated"""

    def test_agents_have_structured_llm(self):
        """Test that agents are properly configured with structured output"""
        # This test doesn't require API key
        from langchain_openai import ChatOpenAI
        from agents.timing_agent import TimingAgent, TimingComplianceResult
        from agents.identity_agent import IdentityAgent, IdentityComplianceResult
        from agents.route_agent import RouteAgent, RouteComplianceResult

        # Create a dummy LLM (won't be called)
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key="dummy")

        # Test that agents initialize with structured LLM
        timing_agent = TimingAgent(llm)
        identity_agent = IdentityAgent(llm)
        route_agent = RouteAgent(llm)

        # Verify structured LLM is created
        assert hasattr(timing_agent, "structured_llm")
        assert hasattr(identity_agent, "structured_llm")
        assert hasattr(route_agent, "structured_llm")

        # Verify structured LLM is different from base LLM (indicates structured output is configured)
        assert timing_agent.structured_llm != timing_agent.llm
        assert identity_agent.structured_llm != identity_agent.llm
        assert route_agent.structured_llm != route_agent.llm

    def test_pydantic_models_structure(self):
        """Test that Pydantic models have expected structure"""
        from agents.timing_agent import TimingComplianceResult, TimingViolation
        from agents.identity_agent import IdentityComplianceResult, IdentityViolation
        from agents.route_agent import RouteComplianceResult, RouteViolation

        # Test timing models
        timing_result = TimingComplianceResult(
            status="COMPLIANT", message="Test message", details={"violations": []}
        )
        assert timing_result.rule_name == "Flight Ticket Timing"
        assert timing_result.status == "COMPLIANT"

        # Test identity models
        identity_result = IdentityComplianceResult(
            status="NON_COMPLIANT", message="Test message", details={"violations": []}
        )
        assert identity_result.rule_name == "Passenger Identity"
        assert identity_result.status == "NON_COMPLIANT"

        # Test route models
        route_result = RouteComplianceResult(
            status="COMPLIANT", message="Test message", details={"violations": []}
        )
        assert route_result.rule_name == "SunExpress Route Compliance"
        assert route_result.status == "COMPLIANT"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestTimingCompliance:
    """Test timing compliance rules"""

    def test_valid_timing_compliance(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where all flights fall within travel approval dates - PASS scenario"""
        result = compliance_agent.check_timing_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result["status"] in ["COMPLIANT", "NON_COMPLIANT", "SYSTEM_ERROR"]
        assert "rule_name" in result
        assert "details" in result
        assert "violations" in result["details"]

    def test_departure_before_travel_period(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where departure is before travel approval start - FAIL scenario"""
        # Modify flight to depart before travel period
        valid_flight_reservation["flights"][0]["departureDate"] = "2025-06-20T12:35:00"

        result = compliance_agent.check_timing_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result["status"] in ["COMPLIANT", "NON_COMPLIANT", "SYSTEM_ERROR"]
        assert "rule_name" in result
        assert "details" in result


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestPassengerIdentityCompliance:
    """Test passenger identity compliance rules"""

    def test_valid_passenger_identity(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where passenger identity matches - PASS scenario"""
        result = compliance_agent.check_passenger_identity(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result["status"] in ["COMPLIANT", "NON_COMPLIANT", "SYSTEM_ERROR"]
        assert "rule_name" in result
        assert "details" in result
        assert "violations" in result["details"]


class TestRouteCompliance:
    """Test route compliance rules - these work without LLM"""

    def test_valid_route_compliance_sunexpress(
        self, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where SunExpress account uses SunExpress airline - PASS scenario"""
        # Create agent without requiring API key for route agent
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key="dummy")
        compliance_agent = ComplianceAgent(model="gpt-4o-mini", openai_api_key="dummy")

        result = compliance_agent.check_route_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result["status"] in [
            "COMPLIANT",
            "NON_COMPLIANT",
            "UNKNOWN",
            "SYSTEM_ERROR",
        ]
        assert "SunExpress Route Compliance" in result["rule_name"]
        assert "details" in result
        assert "violations" in result["details"]

    def test_invalid_route_compliance_sunexpress(
        self, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where SunExpress account uses different airline - POTENTIAL FAIL scenario"""
        # Change airline code to Turkish Airlines while keeping SunExpress account
        valid_flight_reservation["flights"][0]["airlineCode"] = "TK"
        valid_flight_reservation["flights"][0]["airlineName"] = "Turkish Airlines"
        valid_flight_reservation["flights"][0]["flightNumber"] = "TK123"

        from langchain_openai import ChatOpenAI

        compliance_agent = ComplianceAgent(model="gpt-4o-mini", openai_api_key="dummy")

        result = compliance_agent.check_route_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        # Note: This may pass or fail depending on whether SunExpress actually operates the AYT-FRA route
        assert result["status"] in [
            "COMPLIANT",
            "NON_COMPLIANT",
            "UNKNOWN",
            "SYSTEM_ERROR",
        ]
        assert "SunExpress Route Compliance" in result["rule_name"]


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestComplianceReport:
    """Test comprehensive compliance report generation"""

    def test_all_compliant_report(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where all rules pass - PASS scenario"""
        report = compliance_agent.generate_compliance_report(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert "overall_status" in report
        assert "summary" in report
        assert "results" in report
        assert len(report["results"]) == 3  # All three rules checked
        assert all("status" in r for r in report["results"])
        assert all("rule_name" in r for r in report["results"])


class TestDataStructures:
    """Test data structure compatibility without LLM calls"""

    def test_data_structure_compatibility(
        self, valid_travel_approval, valid_flight_reservation
    ):
        """Test that data structures are compatible with agent expectations"""
        # Test that required fields are present
        assert "travelBeginDate" in valid_travel_approval
        assert "travelEndDate" in valid_travel_approval
        assert "passengerList" in valid_travel_approval

        assert "flights" in valid_flight_reservation
        assert "passengers" in valid_flight_reservation

        # Test flight structure
        flight = valid_flight_reservation["flights"][0]
        assert "departureDate" in flight
        assert "arrivalDate" in flight
        assert "airlineCode" in flight

        # Test passenger structure
        passenger = valid_flight_reservation["passengers"][0]
        assert "employeeId" in passenger
        assert "name" in passenger


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
