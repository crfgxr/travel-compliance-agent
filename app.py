import streamlit as st
import json
import os
import logging
from dotenv import load_dotenv
from agents import ComplianceAgent, create_llm_client
from utils import (
    validate_openai_key,
    parse_json_input,
    extract_data_from_json,
    format_compliance_result,
    create_sample_data,
)

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # This sends logs to terminal
    ],
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


# Simple notification system using Streamlit's built-in components
def show_notification(message: str, type: str = "info"):
    """Show notification using Streamlit's built-in components and log to terminal"""
    if type == "success":
        st.success(message)
        logger.info(f"✅ {message}")
    elif type == "error":
        st.error(message)
        logger.error(f"❌ {message}")  # Log errors to terminal
    elif type == "warning":
        st.warning(message)
        logger.warning(f"⚠️ {message}")  # Log warnings to terminal
    elif type == "info":
        st.info(message)
        logger.info(f"ℹ️ {message}")
    else:
        st.info(message)
        logger.info(f"ℹ️ {message}")


# Page configuration
st.set_page_config(
    page_title="Travel Compliance Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    logger.info("🚀 Starting Travel Compliance Agent")

    # Header
    st.markdown(
        """
    <div style="background: linear-gradient(90deg, #1f4e79, #2d5aa0); padding: 1rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>✈️ Travel Compliance Agent</h1>
        <p>Automated audit system for travel booking compliance</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar for API key and settings
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Show API key input only if not validated
        if not st.session_state.get("api_key_validated", False):
            # OpenAI API Key input
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value="",
                placeholder="sk-...",
                help="Enter your OpenAI API key to enable AI-powered compliance checking",
            )

            # Automatic validation when API key is provided
            if api_key:
                with st.spinner("🔑 Validating OpenAI API key..."):
                    logger.info("🔑 Validating OpenAI API key...")
                    if validate_openai_key(api_key):
                        st.session_state.api_key_validated = True
                        st.session_state.openai_api_key = (
                            api_key  # Store in session state
                        )
                        show_notification("API Key validated successfully!", "success")
                        os.environ["OPENAI_API_KEY"] = api_key
                        logger.info("✅ OpenAI API key validated successfully")
                        st.rerun()  # Refresh to hide the input field
                    else:
                        st.session_state.api_key_validated = False
                        show_notification(
                            "Invalid API key. Please check and try again.", "error"
                        )
                        logger.warning("❌ OpenAI API key validation failed")

            # Show warning instruction
            st.warning("💡 Press Enter after entering your key to validate")
        else:
            # Show success message when validated
            st.success("✅ API Key validated successfully!")

        # Model selection
        model_name = st.selectbox(
            "AI Model",
            options=["gpt-4.1-2025-04-14"],
            index=0,
            help="Select the AI model for compliance checking",
        )
        logger.info(f"🤖 Using model: {model_name}")

        st.divider()

        # Sample data / Reset button (only show if API key is validated)
        if st.session_state.get("api_key_validated", False):
            # Check if any data is present (either from session state or manual input)
            any_data_present = (
                st.session_state.get("sample_travel_data", "").strip()
                or st.session_state.get("sample_ticket_data", "").strip()
                or st.session_state.get("manual_data_entered", False)
            )

            if any_data_present:
                # Show reset button when any data is present
                if st.button(
                    "🔄 Reset Data",
                    disabled=st.session_state.get("loading_sample", False),
                    help="Clear all JSON input data",
                ):
                    st.session_state.sample_travel_data = ""
                    st.session_state.sample_ticket_data = ""
                    st.session_state.manual_data_entered = False
                    # Force text areas to refresh by updating their keys
                    st.session_state.travel_input = ""
                    st.session_state.ticket_input = ""
                    logger.info("🔄 All JSON data reset by user")
                    show_notification("All data cleared successfully!", "info")
                    st.rerun()
            else:
                # Show load button when no data is present
                if st.button(
                    "📋 Load Sample Data",
                    disabled=st.session_state.get("loading_sample", False),
                    help="Load example travel approval and ticket data",
                ):
                    st.session_state.loading_sample = True
                    with st.spinner("Loading sample data..."):
                        logger.info("📋 Loading sample data...")
                        sample_travel, sample_ticket = create_sample_data()

                        if sample_travel is None or sample_ticket is None:
                            show_notification(
                                "Failed to load sample data. Check that TravelApproval.json and Ticket.json files exist.",
                                "error",
                            )
                            logger.error("❌ Failed to load sample data files")
                        else:
                            st.session_state.sample_travel_data = json.dumps(
                                sample_travel, indent=2
                            )
                            st.session_state.sample_ticket_data = json.dumps(
                                sample_ticket, indent=2
                            )
                            # Also set the text area keys to display the data
                            st.session_state.travel_input = (
                                st.session_state.sample_travel_data
                            )
                            st.session_state.ticket_input = (
                                st.session_state.sample_ticket_data
                            )
                            show_notification(
                                "Sample data loaded successfully!", "success"
                            )
                            logger.info("✅ Sample data loaded successfully")
                    st.session_state.loading_sample = False
                    st.rerun()

    # Main content area
    if not st.session_state.get("api_key_validated", False):
        show_notification(
            "Please enter a valid OpenAI API key in the sidebar to continue.",
            "warning",
        )
        logger.warning("⚠️ No valid OpenAI API key provided")
        return

    # Initialize agents
    logger.info("🤖 Initializing AI agents...")
    llm = create_llm_client(
        model=model_name,
        temperature=0,
        openai_api_key=st.session_state.get("openai_api_key"),
    )
    compliance_agent = ComplianceAgent(llm)
    logger.info("✅ AI agents initialized successfully")

    # Main compliance check content
    st.header("Travel Compliance Audit")

    col1, col2 = st.columns(2)

    def on_travel_change():
        # Track that user has manually entered data
        if not st.session_state.get("manual_data_entered", False):
            st.session_state.manual_data_entered = True
        # Sync session state only if different
        current_data = st.session_state.get("sample_travel_data", "")
        if current_data != st.session_state.travel_input:
            st.session_state.sample_travel_data = st.session_state.travel_input

    def on_ticket_change():
        # Track that user has manually entered data
        if not st.session_state.get("manual_data_entered", False):
            st.session_state.manual_data_entered = True
        # Sync session state only if different
        current_data = st.session_state.get("sample_ticket_data", "")
        if current_data != st.session_state.ticket_input:
            st.session_state.sample_ticket_data = st.session_state.ticket_input

    with col1:
        st.subheader("Travel Approval Data")
        travel_approval_input = st.text_area(
            "Paste Travel Approval JSON",
            height=300,
            placeholder='{\n  "data": {\n    "travelCity": "Frankfurt",\n    "travelCountry": "Germany",\n    "travelBeginDate": "2025-06-22T09:00:00",\n    "travelEndDate": "2025-06-26T09:00:00",\n    "passengerList": [...]\n  }\n}',
            help="Enter the travel approval JSON data",
            on_change=on_travel_change,
            key="travel_input",
        )

    with col2:
        st.subheader("Flight Ticket Data")
        ticket_data_input = st.text_area(
            "Paste Flight Ticket JSON",
            height=300,
            placeholder='{\n  "data": {\n    "flights": [\n      {\n        "bookingId": "TIC-457855",\n        "flights": [...],\n        "passengers": [...]\n      }\n    ]\n  }\n}',
            help="Enter the flight ticket JSON data",
            on_change=on_ticket_change,
            key="ticket_input",
        )

    st.divider()

    # Check if either input is empty (button should be disabled if any field is empty)
    either_input_empty = (
        not travel_approval_input.strip() or not ticket_data_input.strip()
    )

    # Compliance check button
    if st.button(
        "🚀 Run Compliance Audit",
        type="primary",
        disabled=st.session_state.get("running_audit", False) or either_input_empty,
    ):
        if travel_approval_input and ticket_data_input:
            st.session_state.running_audit = True
            st.session_state.audit_completed = False  # Reset completion flag
            st.session_state.travel_input_data = travel_approval_input
            st.session_state.ticket_input_data = ticket_data_input
            st.rerun()

    # Handle audit execution if running_audit is True
    if st.session_state.get("running_audit", False):
        travel_approval_input = st.session_state.get("travel_input_data", "")
        ticket_data_input = st.session_state.get("ticket_input_data", "")

        if travel_approval_input and ticket_data_input:
            logger.info("🚀 Starting compliance audit...")
            with st.spinner("Running compliance audit..."):
                # Parse JSON data
                travel_data = parse_json_input(travel_approval_input)
                ticket_data = parse_json_input(ticket_data_input)

                # Check for JSON parsing errors
                json_errors = []
                if travel_data is None:
                    json_errors.append("Travel Approval JSON is invalid or empty")
                if ticket_data is None:
                    json_errors.append("Flight Ticket JSON is invalid or empty")

                if json_errors:
                    show_notification("JSON parsing failed", "error")
                    for error in json_errors:
                        show_notification(error, "error")
                    st.session_state.running_audit = False
                elif travel_data and ticket_data:
                    logger.info("📊 Extracting data for LLM processing...")
                    # Extract data from JSON structures
                    travel_approval, flight_reservations = extract_data_from_json(
                        travel_data, ticket_data
                    )

                    if travel_approval and flight_reservations:
                        logger.info("🔍 Running compliance checks...")
                        # Generate compliance report
                        report = compliance_agent.generate_compliance_report(
                            travel_approval, flight_reservations
                        )

                        logger.info(
                            f"📊 Compliance audit completed: {report['overall_status']}"
                        )
                        logger.info(f"Results: {len(report['results'])} rules checked")

                        # Display results
                        st.header("📊 Compliance Audit Results")

                        # Overall status
                        status_class = f"status-{report['overall_status'].lower().replace('_', '-')}"
                        st.markdown(
                            f'<div class="{status_class}"><h3>{report["summary"]}</h3></div>',
                            unsafe_allow_html=True,
                        )

                        # Log each rule result
                        for result in report["results"]:
                            logger.info(
                                f"Rule '{result.get('rule_name', 'Unknown')}': {result.get('status', 'Unknown')} - {result.get('message', 'No message')}"
                            )
                            with st.expander(
                                format_compliance_result(result),
                                expanded=(
                                    result.get("status")
                                    in ["NON_COMPLIANT", "SYSTEM_ERROR"]
                                ),
                            ):
                                details = result.get("details", {})
                                violations = details.get("violations", [])

                                if violations:
                                    st.subheader("🚨 Issues Found:")
                                    for i, violation in enumerate(violations, 1):
                                        # Display user-friendly violation information
                                        st.markdown(f"**Issue #{i}:**")

                                        # Check if this is a technical error or actual violation
                                        if details.get("error_type"):
                                            st.error(
                                                f"**System Error:** {details.get('error_message', 'Unknown error')}"
                                            )
                                            if details.get("raw_response"):
                                                with st.expander(
                                                    "🔍 Raw AI Response (for debugging)"
                                                ):
                                                    st.code(details.get("raw_response"))
                                        else:
                                            # Display actual compliance violation
                                            if violation.get("reason"):
                                                st.warning(
                                                    f"**Problem:** {violation.get('reason')}"
                                                )

                                            # Show specific details based on violation type
                                            if violation.get("flight_number"):
                                                st.info(
                                                    f"**Flight:** {violation.get('flight_number')}"
                                                )

                                            if violation.get("passenger_name"):
                                                st.info(
                                                    f"**Passenger:** {violation.get('passenger_name')}"
                                                )

                                            if violation.get(
                                                "actual_airline"
                                            ) and violation.get("required_airline"):
                                                st.info(
                                                    f"**Airline Used:** {violation.get('actual_airline_name', violation.get('actual_airline'))}"
                                                )
                                                st.info(
                                                    f"**Required Airline:** {violation.get('required_airline_name', violation.get('required_airline'))}"
                                                )

                                            if violation.get(
                                                "departure_date"
                                            ) or violation.get("arrival_date"):
                                                if violation.get("departure_date"):
                                                    st.info(
                                                        f"**Departure:** {violation.get('departure_date')}"
                                                    )
                                                if violation.get("arrival_date"):
                                                    st.info(
                                                        f"**Arrival:** {violation.get('arrival_date')}"
                                                    )
                                                if violation.get("approved_period"):
                                                    st.info(
                                                        f"**Approved Period:** {violation.get('approved_period')}"
                                                    )

                                            if violation.get("recommendation"):
                                                st.success(
                                                    f"**💡 How to Fix:** {violation.get('recommendation')}"
                                                )

                                            # Show raw violation data in collapsed section for debugging
                                            with st.expander("🔍 Technical Details"):
                                                st.json(violation)

                                        if i < len(violations):
                                            st.divider()

                                        logger.warning(
                                            f"Violation in {result.get('rule_name', 'Unknown')}: {violation.get('reason', str(violation))}"
                                        )
                                else:
                                    st.success("✅ No issues found for this rule.")

                        logger.info(
                            "✅ Compliance audit completed and results displayed"
                        )
                        # Set flag to prevent rerun and mark audit as completed
                        st.session_state.running_audit = False
                        st.session_state.audit_completed = True
        else:
            show_notification(
                "Please provide both travel approval and ticket data.", "error"
            )
            logger.error("❌ Missing travel approval or ticket data")
            st.session_state.running_audit = False


if __name__ == "__main__":
    main()
