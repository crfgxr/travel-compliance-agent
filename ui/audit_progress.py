import streamlit as st
import logging
import time
from agents import ComplianceAgent
from utils import parse_json_input, extract_data_from_json
from .common import show_notification, format_compliance_result

logger = logging.getLogger(__name__)


def render_audit_progress():
    """Render the audit progress state"""
    st.header("Travel Compliance Audit")

    # If audit is completed and we have results, just show them
    if st.session_state.get("audit_completed", False) and st.session_state.get(
        "audit_report"
    ):
        st.success("✅ Audit Completed - Review results below")
        st.markdown("---")
        _render_results_inline(st.session_state.audit_report)
        return

    travel_approval_input = st.session_state.get("travel_input_data", "")
    ticket_data_input = st.session_state.get("ticket_input_data", "")

    if travel_approval_input and ticket_data_input:
        logger.info("🚀 Starting compliance audit...")

        # Show progress UI immediately - NOT inside a spinner
        st.subheader("🔄 Running Compliance Audit")
        progress_bar = st.progress(0)
        status_text = st.empty()
        current_job_text = st.empty()

        # Initial status
        status_text.text("Initializing audit...")

        # Small delay to ensure UI renders before processing starts
        time.sleep(0.1)

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
            status_text.text("Extracting data for processing...")

            # Extract data from JSON structures
            travel_approval, flight_reservations = extract_data_from_json(
                travel_data, ticket_data
            )

            if travel_approval and flight_reservations:
                logger.info("🔍 Running compliance checks...")
                status_text.text("Starting compliance checks...")

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
                model_name = st.session_state.get("selected_model")

                # Create ComplianceAgent with proper parameters
                compliance_agent = ComplianceAgent(
                    model=model_name,
                    openai_api_key=st.session_state.get("openai_api_key"),
                )

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

                # Trigger a controlled rerun to update sidebar state
                st.rerun()
    else:
        show_notification(
            "Please provide both travel approval and ticket data.", "error"
        )
        logger.error("❌ Missing travel approval or ticket data")
        st.session_state.running_audit = False
        st.session_state.loading_sample = False


def _render_results_inline(report):
    """Render audit results inline within the progress component"""
    # Display results header
    st.header("📊 Compliance Audit Results")

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
            # Handle both old format (details.violations) and new format (result.violations)
            violations = details.get("violations", []) or result.get("violations", [])

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
                                f"**💡 How to Fix:** {violation.get('recommendation')}"
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
