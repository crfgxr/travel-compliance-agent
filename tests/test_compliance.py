import pytest
import json
from datetime import datetime
from src.models import *
from agents import ComplianceAgent


@pytest.fixture
def compliance_agent():
    """Create a compliance agent for testing"""
    return ComplianceAgent(
        model="gpt-4o-mini", temperature=0, openai_api_key="test-key-for-testing"
    )


@pytest.fixture
def valid_travel_approval():
    """Create a valid travel approval for testing"""
    return TravelApproval(
        travelCity="Frankfurt",
        travelCountry="Germany",
        travelBeginDate=datetime(2025, 6, 22, 9, 0),
        travelEndDate=datetime(2025, 6, 26, 9, 0),
        travelReason="Business",
        passengerList=[
            Passenger(
                name="Mr. Jhon",
                surname="Doe",
                gender="Male",
                emailAddress="jhon.doe@sunexpress.com",
                employeeId="00000001",
                userType="user",
            )
        ],
        Status="Approved",
    )


@pytest.fixture
def valid_flight_reservation():
    """Create a valid flight reservation for testing"""
    return FlightReservation(
        bookingId="TIC-457855",
        confirmationNumber="SRWK64",
        requestorUser="MR.JHON DOE",
        accountName="SunExpress",
        flights=[
            Flight(
                flightNo="XQ141",
                airlineCompanyCode="XQ",
                cabinClass="Economy",
                departureDate=datetime(2025, 6, 24, 12, 35),
                departureTime="12:35:00",
                arrivalDate=datetime(2025, 6, 24, 14, 15),
                arrivalTime="14:15:00",
                departureAirPortCode="AYT",
                departureAirportCodeCountryCode="TR",
                departureAirportCodeCity="Antalya",
                arrivalAirPortCode="FRA",
                arrivalAirportCodeCountryCode="DE",
                arrivalAirportCodeCity="Frankfurt",
                directionType="departure",
            )
        ],
        passengers=[
            Passenger(
                name="Mr. Jhon",
                surname="Doe",
                gender="Male",
                emailAddress="jhon.doe@sunexpress.com",
                employeeId="00000001",
                userType="user",
            )
        ],
    )


class TestTimingCompliance:
    """Test timing compliance rules"""

    def test_valid_timing_compliance(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where all flights fall within travel approval dates - PASS scenario"""
        result = compliance_agent.check_timing_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.COMPLIANT
        assert "All flights fall within approved travel period" in result.message
        assert result.rule_name == "Flight Ticket Timing"

    def test_departure_before_travel_period(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where departure is before travel approval start - FAIL scenario"""
        # Modify flight to depart before travel period
        valid_flight_reservation.flights[0].departureDate = datetime(
            2025, 6, 20, 12, 35
        )

        result = compliance_agent.check_timing_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.NON_COMPLIANT
        assert "timing violations" in result.message
        assert result.details is not None
        assert len(result.details["violations"]) > 0

    def test_arrival_after_travel_period(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where arrival is after travel approval end - FAIL scenario"""
        # Modify flight to arrive after travel period
        valid_flight_reservation.flights[0].arrivalDate = datetime(2025, 6, 28, 14, 15)

        result = compliance_agent.check_timing_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.NON_COMPLIANT
        assert "timing violations" in result.message


class TestPassengerIdentityCompliance:
    """Test passenger identity compliance rules"""

    def test_valid_passenger_identity(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where passenger identity matches - PASS scenario"""
        result = compliance_agent.check_passenger_identity(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.COMPLIANT
        assert "All passenger identities match approval" in result.message

    def test_passenger_not_in_approval(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where passenger is not in approval list - FAIL scenario"""
        # Add unauthorized passenger
        valid_flight_reservation.passengers.append(
            Passenger(
                name="Jane",
                surname="Smith",
                gender="Female",
                emailAddress="jane.smith@example.com",
                employeeId="00000002",
                userType="user",
            )
        )

        result = compliance_agent.check_passenger_identity(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.NON_COMPLIANT
        assert "identity issues" in result.message
        assert result.details is not None

    def test_employee_id_mismatch(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where employee ID doesn't match - FAIL scenario"""
        # Change employee ID in ticket but keep name same
        valid_flight_reservation.passengers[0].employeeId = "99999999"

        result = compliance_agent.check_passenger_identity(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.NON_COMPLIANT
        assert "identity issues" in result.message


class TestRouteCompliance:
    """Test route compliance rules"""

    def test_valid_route_compliance_sunexpress(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where SunExpress account uses SunExpress airline - PASS scenario"""
        result = compliance_agent.check_route_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.COMPLIANT
        assert "All routes follow airline compliance rules" in result.message

    def test_invalid_route_compliance_sunexpress(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where SunExpress account uses different airline - FAIL scenario"""
        # Change airline code to Turkish Airlines while keeping SunExpress account
        valid_flight_reservation.flights[0].airlineCompanyCode = "TK"
        valid_flight_reservation.flights[0].flightNo = "TK123"

        result = compliance_agent.check_route_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.NON_COMPLIANT
        assert "route compliance violations" in result.message
        assert result.details is not None
        assert len(result.details["violations"]) > 0

    def test_non_sunexpress_account_compliance(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where non-SunExpress account can use any airline - PASS scenario"""
        # Change account name to non-SunExpress
        valid_flight_reservation.accountName = "Turkish Airlines"
        valid_flight_reservation.flights[0].airlineCompanyCode = "TK"
        valid_flight_reservation.flights[0].flightNo = "TK123"

        result = compliance_agent.check_route_compliance(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert result.status == ComplianceStatus.COMPLIANT


class TestComplianceReport:
    """Test comprehensive compliance report generation"""

    def test_all_compliant_report(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case where all rules pass - PASS scenario"""
        report = compliance_agent.generate_compliance_report(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert report.overall_status == ComplianceStatus.COMPLIANT
        assert "PASSED" in report.summary
        assert len(report.results) == 3  # All three rules checked
        assert all(r.status == ComplianceStatus.COMPLIANT for r in report.results)

    def test_mixed_compliance_report(
        self, compliance_agent, valid_travel_approval, valid_flight_reservation
    ):
        """Test case with mixed compliance results - FAIL scenario"""
        # Create violations in multiple rules
        valid_flight_reservation.flights[0].departureDate = datetime(
            2025, 6, 20, 12, 35
        )  # Timing violation
        valid_flight_reservation.flights[0].airlineCompanyCode = "TK"  # Route violation

        report = compliance_agent.generate_compliance_report(
            valid_travel_approval, [valid_flight_reservation]
        )

        assert report.overall_status == ComplianceStatus.NON_COMPLIANT
        assert "FAILED" in report.summary
        assert len(report.results) == 3

        # Count violations
        violations = [
            r for r in report.results if r.status == ComplianceStatus.NON_COMPLIANT
        ]
        assert len(violations) >= 2  # At least timing and route violations


# Integration test with real JSON data structure
class TestIntegrationWithJsonData:
    """Test integration with actual JSON data structures"""

    def test_with_sample_json_data(self, compliance_agent):
        """Test with JSON data similar to the provided samples"""
        # Sample data similar to the provided JSON files
        travel_approval_data = TravelApproval(
            travelCity="Frankfurt",
            travelCountry="Germany",
            travelBeginDate=datetime(2025, 6, 22, 9, 0),
            travelEndDate=datetime(2025, 6, 26, 9, 0),
            travelReason="Business",
            passengerList=[
                Passenger(
                    name="Mr. Jeo",
                    surname="Doe",
                    gender="Male",
                    emailAddress="nobody@sunexpress.com",
                    employeeId="00000001",
                    userType="user",
                )
            ],
            Status="Approved",
        )

        flight_reservation_data = FlightReservation(
            bookingId="TIC-457855",
            confirmationNumber="SRWK64",
            requestorUser="MR.JHON DOE",
            accountName="SunExpress",
            flights=[
                Flight(
                    flightNo="XQ141",
                    airlineCompanyCode="XQ",
                    cabinClass="S",
                    departureDate=datetime(2025, 6, 24, 12, 35),
                    departureTime="12:35:00",
                    arrivalDate=datetime(2025, 6, 24, 14, 15),
                    arrivalTime="14:15:00",
                    departureAirPortCode="AYT",
                    departureAirportCodeCountryCode="TR",
                    departureAirportCodeCity="Antalya",
                    arrivalAirPortCode="FRA",
                    arrivalAirportCodeCountryCode="DE",
                    arrivalAirportCodeCity="Frankfurt",
                    directionType="departure",
                )
            ],
            passengers=[
                Passenger(
                    name="Mr. Jhon",  # Name mismatch with approval
                    surname="Hoe",  # Surname mismatch
                    gender="Male",
                    emailAddress="hoe@sunexpress.com",
                    employeeId="00000001",
                    userType="user",
                )
            ],
        )

        # This should fail on passenger identity
        report = compliance_agent.generate_compliance_report(
            travel_approval_data, [flight_reservation_data]
        )

        assert report.overall_status == ComplianceStatus.NON_COMPLIANT

        # Find passenger identity result
        identity_result = next(
            r for r in report.results if r.rule_name == "Passenger Identity"
        )
        assert identity_result.status == ComplianceStatus.NON_COMPLIANT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
