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
                value=st.session_state.get("api_key_input", ""),
                placeholder="sk-...",
                help="Enter your OpenAI API key to enable AI-powered compliance checking",
                key="api_key_input_field",
            )

            # Store the input in session state for persistence
            if api_key != st.session_state.get("api_key_input", ""):
                st.session_state.api_key_input = api_key
                # Clear any previous validation state when user changes the key
                if "api_key_validation_attempted" in st.session_state:
                    del st.session_state.api_key_validation_attempted
                if "api_key_validation_error" in st.session_state:
                    del st.session_state.api_key_validation_error

            # Show validation button only if key is entered
            if api_key.strip():
                validate_button = st.button(
                    "🔑 Validate",
                    type="primary",
                    help="Click to validate your API key",
                    disabled=len(api_key.strip()) < 10,  # Basic length check
                    use_container_width=True,
                )

                # Handle validation when button is clicked
                if validate_button:
                    st.session_state.api_key_validation_attempted = True
                    with st.spinner("🔑 Validating OpenAI API key..."):
                        logger.info("🔑 Validating OpenAI API key...")
                        if validate_openai_key(api_key):
                            st.session_state.api_key_validated = True
                            st.session_state.openai_api_key = api_key
                            # Clear temporary states
                            if "api_key_input" in st.session_state:
                                del st.session_state.api_key_input
                            if "api_key_validation_attempted" in st.session_state:
                                del st.session_state.api_key_validation_attempted
                            if "api_key_validation_error" in st.session_state:
                                del st.session_state.api_key_validation_error
                            show_notification(
                                "API Key validated successfully!", "success"
                            )
                            os.environ["OPENAI_API_KEY"] = api_key
                            logger.info("✅ OpenAI API key validated successfully")
                            st.rerun()  # Refresh to hide the input field
                        else:
                            st.session_state.api_key_validated = False
                            st.session_state.api_key_validation_error = (
                                "Invalid API key. Please check and try again."
                            )
                            show_notification(
                                "Invalid API key. Please check and try again.", "error"
                            )
                            logger.warning("❌ OpenAI API key validation failed")

            # Show validation feedback if attempted
            if st.session_state.get(
                "api_key_validation_attempted"
            ) and st.session_state.get("api_key_validation_error"):
                st.error(st.session_state.api_key_validation_error)

            # Show helpful instructions
            if not api_key.strip():
                st.info(
                    "💡 Enter your OpenAI API key above and click 'Validate' to continue"
                )
            elif len(api_key.strip()) < 10:
                st.warning("⚠️ API key seems too short. Please check your key.")
        else:
            # Show success message when validated
            st.success("✅ API Key validated successfully!")

            # Model selection (only show when API key is validated)
            model_name = st.selectbox(
                "AI Model",
                options=["gpt-4.1-2025-04-14"],
                index=0,
                help="Select the AI model for compliance checking",
            )
            # Store selected model in session state
            st.session_state.selected_model = model_name
            logger.info(f"🤖 Using model: {model_name}")

        st.divider()

        # Sample data / Reset button (only show if API key is validated)
        if st.session_state.get("api_key_validated", False):
            # Check if audit is currently running
            audit_running = st.session_state.get("running_audit", False)
            audit_completed = st.session_state.get("audit_completed", False)

            # Show audit status when running
            if audit_running:
                st.info("🔄 Audit in progress...")
            elif audit_completed:
                st.success("✅ Audit Completed!")

            # Check if any data is present (either from session state or manual input)
            any_data_present = (
                st.session_state.get("sample_travel_data", "").strip()
                or st.session_state.get("sample_ticket_data", "").strip()
                or st.session_state.get("manual_data_entered", False)
            )

            if not audit_running:
                if any_data_present:
                    # Show reset button when audit is not running (including after completion)
                    if st.button(
                        "🔄 Reset Data",
                        disabled=st.session_state.get("loading_sample", False),
                        help="Clear all JSON input data",
                    ):
                        # Clear all session state completely
                        st.session_state.sample_travel_data = ""
                        st.session_state.sample_ticket_data = ""
                        st.session_state.manual_data_entered = False
                        st.session_state.audit_completed = False  # Clear audit results
                        st.session_state.audit_report = None  # Clear stored report
                        st.session_state.running_audit = False
                        st.session_state.loading_sample = False
                        st.session_state.audit_failed = (
                            False  # Clear audit failed state
                        )
                        st.session_state.json_errors = []  # Clear stored errors
                        st.session_state.just_reset = (
                            True  # Flag to show clean interface
                        )
                        # Force text areas to refresh by updating their keys
                        st.session_state.travel_input = ""
                        st.session_state.ticket_input = ""
                        # Clear any stored input data from audit
                        if "travel_input_data" in st.session_state:
                            del st.session_state.travel_input_data
                        if "ticket_input_data" in st.session_state:
                            del st.session_state.ticket_input_data
                        logger.info("🔄 All JSON data reset by user")
                        show_notification("All data cleared successfully!", "info")
                        st.rerun()
                else:
                    # Show load button only when audit is not running
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
            "🔑 Please enter a valid OpenAI API key in the sidebar to continue.",
            "warning",
        )
        logger.warning("⚠️ No valid OpenAI API key provided")
        return

    # Determine app state and render accordingly
    app_state = get_app_state()

    if app_state == "reset":
        render_reset_success()
    elif app_state == "running_audit":
        render_audit_progress()
    elif app_state == "audit_failed":
        render_audit_failed()
    elif app_state == "audit_completed":
        render_audit_results()
    else:  # default: input_form
        render_input_form()


def get_app_state():
    """Determine current application state"""
    if st.session_state.get("just_reset", False):
        return "reset"
    elif st.session_state.get("running_audit", False):
        return "running_audit"
    elif st.session_state.get("audit_failed", False):
        return "audit_failed"
    elif st.session_state.get("audit_completed", False) and st.session_state.get(
        "audit_report"
    ):
        return "audit_completed"
    else:
        return "input_form"


def render_reset_success():
    """Render the reset success state"""
    st.session_state.just_reset = False
    st.success("✅ Data cleared successfully! You can now enter new travel data.")
    render_input_form()


def render_input_form():
    """Render the main input form"""
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

    # Compliance check button (only show when not running audit AND not completed)
    if not st.session_state.get("running_audit", False) and not st.session_state.get(
        "audit_completed", False
    ):
        if st.button(
            "🚀 Run Compliance Audit",
            type="primary",
            disabled=either_input_empty,
        ):
            if travel_approval_input and ticket_data_input:
                st.session_state.running_audit = True
                st.session_state.audit_completed = False  # Reset completion flag
                st.session_state.travel_input_data = travel_approval_input
                st.session_state.ticket_input_data = ticket_data_input
                st.rerun()


def render_audit_progress():
    """Render the audit progress state"""
    st.header("Travel Compliance Audit")

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
                st.session_state.loading_sample = False
                st.session_state.audit_failed = True
                st.session_state.json_errors = json_errors
                st.rerun()
            elif travel_data and ticket_data:
                logger.info("📊 Extracting data for LLM processing...")
                # Extract data from JSON structures
                travel_approval, flight_reservations = extract_data_from_json(
                    travel_data, ticket_data
                )

                if travel_approval and flight_reservations:
                    logger.info("🔍 Running compliance checks...")

                    # Create progress tracking section that persists across runs
                    st.subheader("🔄 Running Compliance Audit")

                    # Create persistent progress elements
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    current_job_text = st.empty()

                    # Progress callback function
                    def update_progress(current, total, current_job, description, icon):
                        progress = current / total
                        progress_bar.progress(progress)

                        if current <= total:
                            if current == total:
                                status_text.warning(
                                    f"⌛️ All {total} compliance checks completed, now generating report!"
                                )
                                current_job_text.empty()  # Clear job display when completed
                            else:
                                status_text.text(
                                    f"Progress: {current}/{total} checks completed"
                                )
                                current_job_text.markdown(
                                    f"**{icon} {current_job}**\n{description}"
                                )
                        else:
                            status_text.text(f"Running check {current} of {total}...")
                            current_job_text.markdown(
                                f"**{icon} {current_job}**\n{description}"
                            )

                    # Create compliance agent for this audit session
                    model_name = st.session_state.get(
                        "selected_model", "gpt-4.1-2025-04-14"
                    )
                    llm = create_llm_client(
                        model=model_name,
                        temperature=0,
                        openai_api_key=st.session_state.get("openai_api_key"),
                    )
                    compliance_agent = ComplianceAgent(llm)

                    # Generate compliance report with progress tracking
                    report = compliance_agent.generate_compliance_report(
                        travel_approval,
                        flight_reservations,
                        progress_callback=update_progress,
                    )

                    # Clear progress indicators and show completion
                    progress_bar.progress(1.0)
                    status_text.success("✅ Audit Completed - Review results below")
                    current_job_text.empty()  # Clear the current job display

                    logger.info(
                        f"📊 Compliance audit completed: {report['overall_status']}"
                    )
                    logger.info(f"Results: {len(report['results'])} rules checked")

                    # Store the report in session state and mark as completed
                    st.session_state.audit_report = report
                    st.session_state.running_audit = False
                    st.session_state.audit_completed = True
                    st.session_state.loading_sample = False

                    logger.info("✅ Compliance audit completed and results displayed")

                    # Trigger rerun to transition to results view
                    st.rerun()
    else:
        show_notification(
            "Please provide both travel approval and ticket data.", "error"
        )
        logger.error("❌ Missing travel approval or ticket data")
        st.session_state.running_audit = False
        st.session_state.loading_sample = False


def render_audit_failed():
    """Render the audit failed state with clear recovery options"""
    st.header("❌ Audit Failed")

    # Show the JSON parsing errors
    json_errors = st.session_state.get("json_errors", [])

    if json_errors:
        st.error("**JSON parsing failed. Please fix the following issues:**")
        for i, error in enumerate(json_errors, 1):
            st.write(f"{i}. {error}")
    else:
        st.error("The audit failed due to data parsing issues.")

    st.markdown("---")

    # Show clear recovery options
    st.subheader("🔧 How to Fix This")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Option 1: Fix your JSON data**")
        st.info(
            "• Check for missing commas, brackets, or quotes\n• Validate your JSON structure\n• Make sure all required fields are present"
        )

    with col2:
        st.markdown("**Option 2: Start over with sample data**")
        if st.button(
            "🔄 Reset & Load Sample Data",
            type="primary",
            help="Clear current data and load working sample data",
            use_container_width=True,
        ):
            # Clear all data and load sample
            st.session_state.sample_travel_data = ""
            st.session_state.sample_ticket_data = ""
            st.session_state.manual_data_entered = False
            st.session_state.audit_completed = False
            st.session_state.audit_report = None
            st.session_state.running_audit = False
            st.session_state.loading_sample = False
            st.session_state.audit_failed = False
            st.session_state.json_errors = []
            st.session_state.travel_input = ""
            st.session_state.ticket_input = ""

            # Load sample data
            from utils import create_sample_data

            sample_travel, sample_ticket = create_sample_data()
            if sample_travel and sample_ticket:
                st.session_state.sample_travel_data = json.dumps(
                    sample_travel, indent=2
                )
                st.session_state.sample_ticket_data = json.dumps(
                    sample_ticket, indent=2
                )
                st.session_state.travel_input = st.session_state.sample_travel_data
                st.session_state.ticket_input = st.session_state.sample_ticket_data
                show_notification("Sample data loaded successfully!", "success")

            st.rerun()

    st.markdown("---")

    # Show the input form again for fixing
    st.subheader("📝 Edit Your Data")

    # Get the original data that failed
    travel_data = st.session_state.get("travel_input_data", "")
    ticket_data = st.session_state.get("ticket_input_data", "")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Travel Approval Data** *(fix the issues above)*")
        travel_input = st.text_area(
            "Travel Approval JSON",
            value=travel_data,
            height=300,
            help="Fix the JSON errors shown above",
            key="failed_travel_input",
        )

    with col2:
        st.markdown("**Flight Ticket Data** *(fix the issues above)*")
        ticket_input = st.text_area(
            "Flight Ticket JSON",
            value=ticket_data,
            height=300,
            help="Fix the JSON errors shown above",
            key="failed_ticket_input",
        )

    # Try again button
    either_input_empty = not travel_input.strip() or not ticket_input.strip()

    if st.button(
        "🚀 Try Audit Again",
        type="primary",
        disabled=either_input_empty,
        help="Run the compliance audit with your fixed JSON data",
    ):
        if travel_input and ticket_input:
            st.session_state.running_audit = True
            st.session_state.audit_failed = False
            st.session_state.json_errors = []
            st.session_state.travel_input_data = travel_input
            st.session_state.ticket_input_data = ticket_input
            st.rerun()


def render_audit_results():
    """Render the audit results state"""
    report = st.session_state.get("audit_report")
    if not report:
        return

    # Display results header
    st.header("📊 Compliance Audit Results")

    # Add completion notice
    st.success("✅ Audit Completed - Review results below")
    st.markdown("---")

    # Overall status
    status_class = f"status-{report['overall_status'].lower().replace('_', '-')}"
    st.markdown(
        f'<div class="{status_class}"><h3>{report["summary"]}</h3></div>',
        unsafe_allow_html=True,
    )

    # Log each rule result and display
    for result in report["results"]:
        with st.expander(
            format_compliance_result(result),
            expanded=False,
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
                            st.subheader("🔍 Raw AI Response (for debugging)")
                            st.code(details.get("raw_response"))
                    else:
                        # Display actual compliance violation
                        if violation.get("reason"):
                            st.warning(f"**Problem:** {violation.get('reason')}")

                        # Show specific details based on violation type
                        if violation.get("flight_number"):
                            st.info(f"**Flight:** {violation.get('flight_number')}")

                        if violation.get("passenger_name"):
                            st.info(f"**Passenger:** {violation.get('passenger_name')}")

                        if violation.get("actual_airline") and violation.get(
                            "required_airline"
                        ):
                            st.info(
                                f"**Airline Used:** {violation.get('actual_airline_name', violation.get('actual_airline'))}"
                            )
                            st.info(
                                f"**Required Airline:** {violation.get('required_airline_name', violation.get('required_airline'))}"
                            )

                        if violation.get("departure_date") or violation.get(
                            "arrival_date"
                        ):
                            if violation.get("departure_date"):
                                st.info(
                                    f"**Departure:** {violation.get('departure_date')}"
                                )
                            if violation.get("arrival_date"):
                                st.info(f"**Arrival:** {violation.get('arrival_date')}")
                            if violation.get("approved_period"):
                                st.info(
                                    f"**Approved Period:** {violation.get('approved_period')}"
                                )

                        if violation.get("recommendation"):
                            st.success(
                                f"**💡 How to Fix:** {violation.get('recommendat🔑 Please enter a valid OpenAI API key in the sidebar to continue.ion')}"
                            )

                        # Show raw violation data for debugging
                        st.subheader("🔍 Technical Details")
                        st.json(violation)

                    if i < len(violations):
                        st.divider()

            elif result.get("status") in [
                "SYSTEM_ERROR",
                "json_parse_error",
                "llm_call_error",
            ]:
                # System error occurred - can't determine compliance status
                st.error(
                    "❌ **System Error:** Unable to complete compliance check due to technical issues"
                )
                # Show additional details if available
                if details.get("error_type"):
                    st.info(f"**Error Type:** {details.get('error_type')}")
                if details.get("error_message"):
                    st.info(f"**Error Message:** {details.get('error_message')}")
                if details.get("raw_response"):
                    st.subheader("🔍 Raw AI Response (for debugging)")
                    st.code(details.get("raw_response"))
                    st.info(
                        "💡 **Suggestion:** This appears to be an AI response parsing issue. The rule could not be properly evaluated."
                    )
            elif result.get("status") == "UNKNOWN":
                # API error occurred - can't determine compliance status
                st.warning(
                    "⚠️ **API Issues:** Unable to complete compliance check due to external API problems"
                )
                # Show API error details if available
                if details.get("api_errors"):
                    st.subheader("🔍 API Error Details:")
                    for i, api_error in enumerate(details.get("api_errors", []), 1):
                        st.info(
                            f"**Route #{i}:** {api_error.get('route', 'Unknown route')}"
                        )
                        st.info(f"**Date:** {api_error.get('date', 'Unknown date')}")
                        st.error(
                            f"**Error:** {api_error.get('error', 'Unknown error')}"
                        )
                        if i < len(details.get("api_errors", [])):
                            st.divider()
                if details.get("note"):
                    st.info(f"💡 **Note:** {details.get('note')}")
                else:
                    st.info(
                        "💡 **Note:** This may be a temporary issue. Please try again later or check API connectivity."
                    )
            else:
                st.success("✅ No issues found for this rule.")


if __name__ == "__main__":
    main()


# v0.2 working
