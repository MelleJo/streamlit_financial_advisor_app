"""
File: main.py
Main application file for the AI Hypotheek Assistent (Mortgage Advisor).
This file serves as the entry point and orchestrates the entire application flow,
including the UI setup, service initialization, and handling of different application states
(input collection, additional questions, and results presentation).
"""

import streamlit as st
from transcription_service import TranscriptionService
from gpt_service import GPTService
from question_recorder import render_question_recorder
import ui_components as ui
from app_state import AppState
from openai import OpenAI
from audio_service import AudioService
from streamlit.components.v1 import declare_component
from checklist_analysis_service import ChecklistAnalysisService

# Page config
st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")
ui.apply_custom_css()

# Register the custom component
advice_module = declare_component(
    "advice_module",
    path="components"  # The directory containing the frontend files
)

# Initialize services and state
if 'app_state' not in st.session_state:
    st.session_state.app_state = AppState()

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["API"]["OPENAI_API_KEY"])

if 'enhanced_texts' not in st.session_state:
    st.session_state.enhanced_texts = {}

def initialize_services():
    """Initialize all required services."""
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    return {
        'gpt_service': GPTService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService(),
        'checklist_service': ChecklistAnalysisService(api_key=api_key)
    }

def handle_questions_complete(answers):
    """Handle completion of additional questions."""
    st.session_state.app_state.set_additional_info(answers)
    st.session_state.app_state.set_step("results")
    st.rerun()

def handle_questions_skip():
    """Handle skipping of additional questions."""
    st.session_state.app_state.set_step("results")
    st.rerun()

def process_initial_input(transcript, services, app_state):
    """Process the initial input and determine next steps."""
    if transcript:
        app_state.set_transcript(transcript)
        
        with st.spinner("Transcript wordt geanalyseerd..."):
            # Analyze initial transcript
            analysis = services['gpt_service'].analyze_initial_transcript(transcript)
            
            if analysis:
                app_state.set_missing_info(analysis.get('missing_info', {}))
                if not any(analysis['missing_info'].values()):
                    app_state.set_analysis_complete(True)
                    app_state.set_step("results")
                else:
                    app_state.set_step("additional_questions")
                st.rerun()

def render_input_section(services, app_state):
    """Render the initial input section with multiple input options."""
    st.title("Hypotheekadvies Invoer")
    
    tab1, tab2, tab3 = st.tabs(["🎙️ Opnemen", "📁 Uploaden", "📝 Tekst invoeren"])
    
    with tab1:
        st.write("Neem uw adviesgesprek op")
        audio_bytes = services['audio_service'].record_audio()
        if audio_bytes:
            with st.spinner("Audio wordt verwerkt..."):
                transcript = services['transcription_service'].transcribe(
                    audio_bytes,
                    mode="fast",
                    language="nl"
                )
                if transcript:
                    process_initial_input(transcript, services, app_state)

    with tab2:
        st.write("Upload een audio- of tekstbestand")
        uploaded_file = st.file_uploader(
            "Kies een bestand",
            type=["txt", "docx", "wav", "mp3", "m4a"]
        )
        if uploaded_file:
            with st.spinner("Bestand wordt verwerkt..."):
                if uploaded_file.type.startswith('audio'):
                    transcript = services['transcription_service'].transcribe(
                        uploaded_file,
                        mode="fast",
                        language="nl"
                    )
                else:
                    transcript = uploaded_file.getvalue().decode("utf-8")
                if transcript:
                    process_initial_input(transcript, services, app_state)

    with tab3:
        st.write("Voer de tekst direct in")
        transcript = st.text_area(
            "Plak of typ hier uw tekst:",
            height=300,
            placeholder="Voer hier het transcript van uw adviesgesprek in..."
        )
        if st.button("Analyseer", use_container_width=True):
            process_initial_input(transcript, services, app_state)

def main():
    """Main application flow."""
    st.title("AI Hypotheek Assistent 🏠")
    
    services = initialize_services()
    app_state = st.session_state.app_state
    
    # Main application flow
    if app_state.step == "input":
        render_input_section(services, app_state)
    
    elif app_state.step == "additional_questions":
        # Show original transcript in expander
        with st.expander("📝 Oorspronkelijk transcript"):
            st.write(app_state.transcript)
        
        # Render question recorder for additional information
        render_question_recorder(
            transcription_service=services['transcription_service'],
            on_complete=handle_questions_complete,
            on_skip=handle_questions_skip
        )
    
    elif app_state.step == "results":
        # Process final results
        if not app_state.result:
            with st.spinner("Eindrapport wordt gegenereerd..."):
                result = services['gpt_service'].analyze_transcript(
                    app_state.transcript,
                    app_state
                )
                if result:
                    app_state.set_result(result)
        
        # Display results
        ui.render_results(app_state)
    
    # Reset button
    if st.sidebar.button("Start Opnieuw", use_container_width=True):
        app_state.reset()
        st.rerun()
    
    # Version info in footer
    st.markdown("---")
    st.markdown("*AI Hypotheek Assistent - v0.0.5*")

if __name__ == "__main__":
    main()
