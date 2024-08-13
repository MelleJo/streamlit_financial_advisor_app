import streamlit as st
from gpt_service import GPTService
import ui_components as ui

# Apply custom CSS for better styling
ui.apply_custom_css()

# Initialize GPTService with your API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]
gpt_service = GPTService(api_key=api_key)

# State management to track user flow
if "page" not in st.session_state:
    st.session_state.page = "home"

# Home Screen - Choose Input Type
if st.session_state.page == "home":
    ui.render_home_screen()

# Text Input Screen
elif st.session_state.page == "text_input":
    ui.render_text_input_screen(gpt_service)

# File Upload Screen
elif st.session_state.page == "file_input":
    ui.render_file_input_screen(gpt_service)

# Result Screen
elif st.session_state.page == "results":
    ui.render_result_screen()

# Footer
ui.render_footer()
