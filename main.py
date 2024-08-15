import streamlit as st
from gpt_service import GPTService
import ui_components as ui

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")

ui.apply_custom_css()

api_key = st.secrets["OPENAI_API_KEY"]
gpt_service = GPTService(api_key=api_key)

def main():
    if "page" not in st.session_state:
        st.session_state.page = "home"

    selected = ui.render_navigation()

    if selected == "Home" or st.session_state.page == "home":
        ui.render_home_screen()
    elif selected == "Handmatige Invoer" or st.session_state.page == "input":
        ui.render_input_screen(gpt_service)
    elif selected == "Bestand Uploaden" or st.session_state.page == "upload":
        ui.render_upload_screen(gpt_service)
    elif selected == "Resultaten" or st.session_state.page == "results":
        ui.render_result_screen()

    ui.render_footer()

if __name__ == "__main__":
    main()