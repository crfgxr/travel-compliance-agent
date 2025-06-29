import streamlit as st
import json
import logging

logger = logging.getLogger(__name__)


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


def get_app_state():
    """Determine current application state with better validation"""
    # Check for reset state first
    if st.session_state.get("just_reset", False):
        return "reset"

    # Check for failed state
    if st.session_state.get("audit_failed", False):
        return "audit_failed"

    # Check for completed state (must have both flags and report)
    if (
        st.session_state.get("audit_completed", False)
        and st.session_state.get("audit_report") is not None
    ):
        return "audit_completed"

    # Check for running state (must have input data)
    if (
        st.session_state.get("running_audit", False)
        and st.session_state.get("travel_input_data")
        and st.session_state.get("ticket_input_data")
    ):
        return "running_audit"

    # Default to input form (also handles inconsistent states)
    return "input_form"


def reset_app_state():
    """Reset all application state more thoroughly"""
    keys_to_clear = [
        "sample_travel_data",
        "sample_ticket_data",
        "manual_data_entered",
        "audit_completed",
        "audit_report",
        "running_audit",
        "loading_sample",
        "audit_failed",
        "json_errors",
        "travel_input",
        "ticket_input",
        "travel_input_data",
        "ticket_input_data",
    ]

    # Clear all keys atomically
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Set reset flag last
    st.session_state.just_reset = True


def render_app_header(version: str = None):
    """Render the application header"""
    version_html = (
        f"<p style='font-size: 0.9em; margin-top: 0.5rem; opacity: 0.8;'>Version {version}</p>"
        if version
        else ""
    )

    st.markdown(
        f"""
    <div style="background: linear-gradient(90deg, #1f4e79, #2d5aa0); padding: 1rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>✈️ Travel Compliance Agent</h1>
        <p>Automated audit system for travel booking compliance</p>
        {version_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def format_compliance_result(result: dict) -> str:
    """Format compliance result for display"""
    status_emoji = {
        "COMPLIANT": "✅",
        "NON_COMPLIANT": "❌",
        "WARNING": "⚠️",
        "SYSTEM_ERROR": "🚨",
        "json_parse_error": "🚨",
        "llm_call_error": "🚨",
    }

    status = result.get("status", "UNKNOWN")
    rule_name = result.get("rule_name", "Unknown Rule")
    message = result.get("message", "No message")

    # Special handling for error statuses to make them clearer
    if status in ["json_parse_error", "llm_call_error", "SYSTEM_ERROR"]:
        return f"{status_emoji.get(status, '❓')} **{rule_name}**: Failed to parse LLM response as valid JSON"

    return f"{status_emoji.get(status, '❓')} **{rule_name}**: {message}"


def create_sample_data() -> tuple:
    """Load sample data from JSON files"""
    try:
        # Load travel approval data from sample_data/TravelApproval.json
        with open("sample_data/TravelApproval.json", "r", encoding="utf-8") as f:
            sample_travel_approval = json.load(f)

        # Load ticket data from sample_data/Ticket.json
        with open("sample_data/Ticket.json", "r", encoding="utf-8") as f:
            sample_ticket_data = json.load(f)

        return sample_travel_approval, sample_ticket_data

    except FileNotFoundError as e:
        error_msg = f"Sample data file not found: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return None, None
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing sample data JSON: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return None, None
