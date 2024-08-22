import streamlit as st
from gpt_service import GPTService
from audio_service import AudioService
from transcription_service import TranscriptionService
import ui_components as ui
from app_state import AppState

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")

ui.apply_custom_css()

def initialize_services():
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    return {
        'gpt_service': GPTService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService()
    }

def main():
    st.title("AI Hypotheek Assistent 🏠")
    st.write("Testversie 0.0.1.")

    services = initialize_services()
    
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()

    ui.render_progress_bar(st.session_state.app_state)

    current_step = st.session_state.app_state.step

    if current_step == "choose_method":
        ui.render_choose_method(st.session_state.app_state)
    elif current_step == "upload":
        ui.render_upload(st.session_state.app_state, services)
    elif current_step == "results":
        ui.render_results(st.session_state.app_state)

    # Check if the step has changed
    if current_step != st.session_state.app_state.step:
        st.rerun()

if __name__ == "__main__":
    main()