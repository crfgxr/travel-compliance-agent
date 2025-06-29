import streamlit as st
import json
from .common import show_notification, create_sample_data


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
