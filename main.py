import streamlit as st
from transcription_service import TranscriptionService
from conversation_service import ConversationService
from question_recorder import render_question_recorder
import ui_components as ui
from app_state import AppState
from openai import OpenAI
from audio_service import AudioService

# Page config
st.set_page_config(page_title="AI Hypotheek Assistent", page_icon="🏠", layout="wide")
ui.apply_custom_css()

# Initialize services and state
if 'app_state' not in st.session_state:
    st.session_state.app_state = AppState()

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["API"]["OPENAI_API_KEY"])

INITIAL_QUESTIONS = [
    {
        "question": "Wat is het gewenste leningbedrag voor de hypotheek?",
        "context": "Dit helpt ons om de juiste hypotheekconstructie te bepalen.",
        "category": "leningdeel"
    },
    {
        "question": "Heeft u interesse in een NHG (Nationale Hypotheek Garantie)?",
        "context": "NHG biedt extra zekerheid en mogelijk een lagere rente.",
        "category": "leningdeel"
    },
    {
        "question": "Welke looptijd heeft uw voorkeur voor de hypotheek?",
        "context": "De standaard looptijd is 30 jaar, maar dit kan worden aangepast.",
        "category": "leningdeel"
    },
    {
        "question": "Wat is uw voorkeur voor de rentevaste periode?",
        "context": "Dit bepaalt hoe lang uw rente vast staat en beïnvloedt uw maandlasten.",
        "category": "leningdeel"
    },
    {
        "question": "Hoe ziet u de risico's bij eventuele werkloosheid?",
        "context": "Dit helpt ons bij het adviseren over werkloosheidsverzekeringen.",
        "category": "werkloosheid"
    },
    {
        "question": "Wat zijn uw wensen voor de periode na pensionering?",
        "context": "Dit helpt ons bij het plannen van uw hypotheek in relatie tot AOW en pensioen.",
        "category": "aow"
    }
]

def initialize_services():
    """Initialize all required services."""
    api_key = st.secrets.API.get("OPENAI_API_KEY")
    return {
        'gpt_service': ConversationService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService()
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
            questions=INITIAL_QUESTIONS,
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