import streamlit as st
from gpt_service import GPTService
import ui_components as ui

# Apply custom CSS
ui.apply_custom_css()

# Render Sidebar
ui.render_sidebar()

# Initialize GPTService with your API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]
gpt_service = GPTService(api_key=api_key)

# Render Tabs (Main Content)
ui.render_tabs(gpt_service)

# Render Footer
ui.render_footer()
