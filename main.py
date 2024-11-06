import streamlit as st
from gpt_service import GPTService
from audio_service import AudioService
from transcription_service import TranscriptionService
import ui_components as ui
from app_state import AppState
from openai import OpenAI

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")
ui.apply_custom_css()

# Initialiseer OpenAI client als deze nog niet bestaat
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["API"]["OPENAI_API_KEY"])

# Initialiseer dictionary voor verbeterde teksten
if 'enhanced_texts' not in st.session_state:
    st.session_state.enhanced_texts = {}



def initialize_services():
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    return {
        'gpt_service': GPTService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService()
    }

def main():
    st.title("AI Hypotheek Assistent 🏠")
    st.write("Versie 0.0.2")

    services = initialize_services()
    
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()

    ui.render_progress_bar(st.session_state.app_state)

    current_step = st.session_state.app_state.step

    if current_step == "select_persons":
        ui.render_person_selection(st.session_state.app_state)
    elif current_step == "person_details":
        ui.render_person_details(st.session_state.app_state)
    elif current_step == "choose_method":
        ui.render_choose_method(st.session_state.app_state)
    elif current_step == "upload":
        ui.render_upload(st.session_state.app_state, services)
    elif current_step == "results":
        ui.render_results(st.session_state.app_state)

    # Show version info in footer
    st.markdown("---")
    st.markdown("*AI Hypotheek Assistent - v0.0.2*")

    # Check if the step has changed
    if current_step != st.session_state.app_state.step:
        st.rerun()

if __name__ == "__main__":
    main()