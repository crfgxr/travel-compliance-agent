import streamlit as st
import logging
from agents import ComplianceAgent
from utils import parse_json_input, extract_data_from_json
from .common import show_notification

logger = logging.getLogger(__name__)


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

                    # Create ComplianceAgent with proper parameters
                    compliance_agent = ComplianceAgent(
                        model=model_name,
                        temperature=0,
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

                    # Trigger rerun to transition to results view
                    st.rerun()
    else:
        show_notification(
            "Please provide both travel approval and ticket data.", "error"
        )
        logger.error("❌ Missing travel approval or ticket data")
        st.session_state.running_audit = False
        st.session_state.loading_sample = False
