import streamlit as st
from gpt_service import GPTService
from audio_service import AudioService
from transcription_service import TranscriptionService
import ui_components as ui
import logging
from app_state import AppState

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")

ui.apply_custom_css()

@st.cache_resource
def initialize_services():
    if 'API' not in st.secrets:
        raise ValueError("API configuration is missing in secrets. Please check your secrets.toml file.")
    
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing in API secrets. Please check your configuration.")
    
    return {
        'gpt_service': GPTService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService()
    }

def main():
    try:
        services = initialize_services()
        
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState()

        ui.render_progress_bar(st.session_state.app_state)

        if st.session_state.app_state.step == "choose_method":
            ui.render_choose_method(st.session_state.app_state)
        elif st.session_state.app_state.step == "upload":
            ui.render_upload(st.session_state.app_state, services)
        elif st.session_state.app_state.step == "results":
            ui.render_results(st.session_state.app_state)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        st.error("An unexpected error occurred. Please try again later or contact support.")

if __name__ == "__main__":
    main()