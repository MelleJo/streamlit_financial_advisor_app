import streamlit as st
from gpt_service import GPTService
from audio_service import AudioService
from transcription_service import TranscriptionService
from conversation_service import ConversationService
from conversation_ui import render_conversation_ui
import ui_components as ui
from app_state import AppState
from openai import OpenAI

st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")
ui.apply_custom_css()

# Initialize services and state
if 'app_state' not in st.session_state:
    st.session_state.app_state = AppState()

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["API"]["OPENAI_API_KEY"])

def initialize_services():
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    return {
        'gpt_service': GPTService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService(),
        'conversation_service': ConversationService(api_key=api_key)
    }

def process_input(transcript, services, app_state):
    """Process initial input and start conversation if needed"""
    if transcript:
        app_state.set_transcript(transcript)
        
        with st.spinner("Transcript wordt geanalyseerd..."):
            # Analyze transcript for missing information
            analysis = services['conversation_service'].analyze_initial_transcript(transcript)
            
            if analysis:
                app_state.set_missing_info(analysis.get('missing_info', {}))
                
                # Add initial AI message if there's a next question
                if analysis.get('next_question'):
                    context = analysis.get('context', '')
                    message = f"{analysis['next_question']}\n\n{context if context else ''}"
                    app_state.add_message(message, is_ai=True)
                
                # If no missing information, proceed to results
                if not any(analysis['missing_info'].values()):
                    app_state.set_analysis_complete(True)
                    app_state.set_step("results")
                else:
                    app_state.set_step("conversation")
            
            st.rerun()

def render_input_section(services, app_state):
    st.title("Hypotheekadvies Invoer")
    
    tab1, tab2, tab3 = st.tabs(["🎙️ Opnemen", "📁 Uploaden", "📝 Tekst invoeren"])
    
    with tab1:
        st.write("Neem uw adviesgesprek op")
        audio_bytes = services['audio_service'].record_audio()
        if audio_bytes:
            with st.spinner("Audio wordt verwerkt..."):
                transcript = services['transcription_service'].transcribe(audio_bytes)
                if transcript:
                    process_input(transcript, services, app_state)

    with tab2:
        st.write("Upload een audio- of tekstbestand")
        uploaded_file = st.file_uploader(
            "Kies een bestand",
            type=["txt", "docx", "wav", "mp3", "m4a"]
        )
        if uploaded_file:
            with st.spinner("Bestand wordt verwerkt..."):
                if uploaded_file.type.startswith('audio'):
                    transcript = services['transcription_service'].transcribe(uploaded_file)
                else:
                    transcript = uploaded_file.getvalue().decode("utf-8")
                if transcript:
                    process_input(transcript, services, app_state)

    with tab3:
        st.write("Voer de tekst direct in")
        transcript = st.text_area(
            "Plak of typ hier uw tekst:",
            height=300,
            placeholder="Voer hier het transcript van uw adviesgesprek in..."
        )
        if st.button("Analyseer", use_container_width=True):
            process_input(transcript, services, app_state)

def main():
    st.title("AI Hypotheek Assistent 🏠")
    
    services = initialize_services()
    app_state = st.session_state.app_state
    
    # Main application flow
    if app_state.step == "input":
        render_input_section(services, app_state)
    
    elif app_state.step == "conversation":
        # Show original transcript in expander
        with st.expander("Oorspronkelijk transcript"):
            st.write(app_state.transcript)
        
        # Render conversation interface
        render_conversation_ui(app_state, services['conversation_service'])
    
    elif app_state.step == "results":
        # Process final results using GPT service
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
    st.markdown("*AI Hypotheek Assistent - v0.0.4*")

if __name__ == "__main__":
    main()