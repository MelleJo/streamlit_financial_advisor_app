import streamlit as st
from gpt_service import GPTService
import ui_components as ui

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")

ui.apply_custom_css()

# Check if API configuration exists
if 'API' not in st.secrets:
    st.error("API configuration is missing in secrets. Please check your secrets.toml file.")
else:
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY is missing in API secrets. Please check your configuration.")
    else:
        gpt_service = GPTService(api_key=api_key)

def main():
    if "step" not in st.session_state:
        st.session_state.step = "choose_method"

    ui.render_progress_bar()

    if st.session_state.step == "choose_method":
        ui.render_choose_method()
    elif st.session_state.step == "upload":
        ui.render_upload(gpt_service)
    elif st.session_state.step == "results":
        ui.render_results()

if __name__ == "__main__":
    main()