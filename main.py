import streamlit as st
from gpt_service import GPTService
import ui_components as ui

# Set page config
st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")

# Apply custom CSS for better styling
ui.apply_custom_css()

# Initialize GPTService with your API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]
gpt_service = GPTService(api_key=api_key)

# State management to track user flow
if "page" not in st.session_state:
    st.session_state.page = "home"

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=Logo", use_column_width=True)
    st.markdown("## AI Hypotheek Assistent")
    st.markdown("Welkom bij de AI Hypotheek Assistent. Deze tool helpt u bij het analyseren van hypotheekgesprekken en het genereren van adviezen.")

# Main content
if st.session_state.page == "home":
    ui.render_home_screen()
elif st.session_state.page == "text_input":
    ui.render_text_input_screen(gpt_service)
elif st.session_state.page == "file_input":
    ui.render_file_input_screen(gpt_service)
elif st.session_state.page == "results":
    ui.render_result_screen()

# Footer
ui.render_footer()