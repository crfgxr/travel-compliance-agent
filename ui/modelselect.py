import streamlit as st
import logging

logger = logging.getLogger(__name__)

# Model pricing information (per million tokens)
MODEL_PRICING = {
    "o4-mini-2025-04-16": {"input": 1.10, "cache": 0.275, "output": 4.40},
    "o3-2025-04-16": {"input": 2.00, "cache": 0.50, "output": 8.00},
    "gpt-4.1-2025-04-14": {"input": 2.00, "cache": 0.50, "output": 8.00},
}


def render_model_select():
    """Render model selection dropdown component"""
    model_name = st.selectbox(
        "Select AI Model",
        options=["o4-mini-2025-04-16", "o3-2025-04-16", "gpt-4.1-2025-04-14"],
        index=0,
        help="Select the AI model for compliance checking",
    )

    # Store selected model in session state
    st.session_state.selected_model = model_name
    logger.info(f"🤖 Using model: {model_name}")

    # Display cost information
    _render_cost_section(model_name)

    return model_name


def _render_cost_section(model_name):
    """Render cost information section for the selected model"""
    if model_name in MODEL_PRICING:
        pricing = MODEL_PRICING[model_name]

        # Simple, clean cost display
        st.markdown(
            f"""
            <div style='background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 4px solid #4CAF50; margin: 10px 0;'>
                <div style='font-size: 14px; color: #555; margin-bottom: 4px;'>💰 Cost per 1M tokens</div>
                <div style='font-size: 16px; font-weight: 500; color: #333;'>
                    Input: <span style='color: #2196F3;'>${pricing['input']:.2f}</span> • 
                    Cache: <span style='color: #4CAF50;'>${pricing['cache']:.3f}</span> • 
                    Output: <span style='color: #FF9800;'>${pricing['output']:.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_selected_model():
    """Get the currently selected model from session state"""
    return st.session_state.get("selected_model", "o4-mini-2025-04-16")
