import streamlit as st


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
