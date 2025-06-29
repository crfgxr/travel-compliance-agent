import streamlit as st
import logging
from dotenv import load_dotenv

# UI imports
from ui import (
    render_app_header,
    render_sidebar,
    show_notification,
    get_app_state,
    render_input_form,
    render_audit_progress,
    render_audit_results,
    render_audit_failed,
)

# Version
__version__ = "0.5.2"

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

# Page configuration
st.set_page_config(
    page_title="Travel Compliance Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    logger.info(f"🚀 Starting Travel Compliance Agent v{__version__}")

    # Render header and sidebar
    render_app_header(__version__)
    render_sidebar()

    # Check API key validation
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
        _render_reset_success()
    elif app_state == "running_audit":
        render_audit_progress()
    elif app_state == "audit_failed":
        render_audit_failed()
    elif app_state == "audit_completed":
        render_audit_results()
    else:  # default: input_form
        render_input_form()


def _render_reset_success():
    """Render reset success and transition to input form"""
    st.session_state.just_reset = False
    st.success("✅ Data cleared successfully! You can now enter new travel data.")
    render_input_form()


if __name__ == "__main__":
    main()


# v0.3
