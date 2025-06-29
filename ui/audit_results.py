import streamlit as st
from .common import format_compliance_result


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
