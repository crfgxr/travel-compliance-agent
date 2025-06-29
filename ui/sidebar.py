import streamlit as st
import os
import json
import logging
from utils import validate_openai_key, get_openai_key_from_env, is_api_key_available
from .common import show_notification, create_sample_data

logger = logging.getLogger(__name__)


def render_sidebar():
    """Render the complete sidebar with configuration and controls"""
    with st.sidebar:
        st.header("⚙️ Configuration")

        _render_api_key_section()
        st.divider()
        _render_data_controls()


def _render_api_key_section():
    """Render API key validation section"""
    # Check if API key is available from environment first
    if not st.session_state.get("api_key_validated", False):
        env_key = get_openai_key_from_env()
        if env_key and not st.session_state.get("env_key_checked", False):
            # Validate the environment key
            if validate_openai_key(env_key):
                st.session_state.api_key_validated = True
                st.session_state.openai_api_key = env_key
                st.session_state.env_key_checked = True
                os.environ["OPENAI_API_KEY"] = env_key
                logger.info("✅ OpenAI API key loaded from environment and validated")
            else:
                st.session_state.env_key_checked = True
                logger.warning("❌ Environment API key is invalid")

    if not st.session_state.get("api_key_validated", False):
        _render_api_key_input()
    else:
        _render_validated_api_key()


def _render_api_key_input():
    """Render API key input and validation"""
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
                    show_notification("API Key validated successfully!", "success")
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
    if st.session_state.get("api_key_validation_attempted") and st.session_state.get(
        "api_key_validation_error"
    ):
        st.error(st.session_state.api_key_validation_error)

    # Show helpful instructions
    if not api_key.strip():
        st.info("💡 Enter your OpenAI API key above and click 'Validate' to continue")
    elif len(api_key.strip()) < 10:
        st.warning("⚠️ API key seems too short. Please check your key.")


def _render_validated_api_key():
    """Render validated API key section with model selection"""
    # Show different message based on source of API key
    env_key = get_openai_key_from_env()
    if env_key and st.session_state.get("env_key_checked", False):
        st.success("✅ API Key loaded from .env file!")
    else:
        st.success("✅ API Key validated successfully!")

    # Model selection (only show when API key is validated)
    model_name = st.selectbox(
        "AI Model",
        options=["gpt-4.1-mini-2025-04-14", "gpt-4.1-2025-04-14"],
        index=0,
        help="Select the AI model for compliance checking",
    )
    # Store selected model in session state
    st.session_state.selected_model = model_name
    logger.info(f"🤖 Using model: {model_name}")


def _render_data_controls():
    """Render data loading and reset controls"""
    if not st.session_state.get("api_key_validated", False):
        return

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
                st.session_state.audit_failed = False  # Clear audit failed state
                st.session_state.json_errors = []  # Clear stored errors
                st.session_state.just_reset = True  # Flag to show clean interface
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
                        show_notification("Sample data loaded successfully!", "success")
                        logger.info("✅ Sample data loaded successfully")
                st.session_state.loading_sample = False
                st.rerun()
