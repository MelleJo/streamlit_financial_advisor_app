import streamlit as st
from gpt_service import GPTService
import ui_components as ui

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")

ui.apply_custom_css()

api_key = st.secrets["OPENAI_API_KEY"]
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