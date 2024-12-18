"""
File: main.py
Main application with integrated FP module.
"""

import streamlit as st
from streamlit_option_menu import option_menu
import logging
from audio_service import AudioService
from transcription_service import TranscriptionService
from gpt_service import GPTService
from fp_integration_service import FPIntegrationService
from app_state import AppState
import main_fp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_services():
    """Initialize all required services."""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OpenAI API key not found in secrets")
            st.stop()
            
        return {
            'gpt_service': GPTService(api_key=api_key),
            'audio_service': AudioService(),
            'transcription_service': TranscriptionService(),
            'fp_service': FPIntegrationService(api_key=api_key)
        }
        
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        st.stop()

def main():
    """Main application flow."""
    # Page config
    st.set_page_config(
        page_title="Veldhuis Advies Assistant",
        page_icon="🏠",
        layout="wide"
    )
    
    # Initialize state and services
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
    
    services = initialize_services()
    app_state = st.session_state.app_state
    
    # Module selection
    selected = option_menu(
        menu_title=None,
        options=["Hypotheek", "Pensioen", "FP"],
        icons=["house", "piggy-bank", "clipboard-data"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    
    # Handle module change
    if app_state.active_module != selected.lower():
        app_state.switch_module(selected.lower())
        st.rerun()
    
    # Render appropriate module
    if app_state.active_module == "hypotheek":
        render_hypotheek_module(app_state, services)
    elif app_state.active_module == "pensioen":
        render_pensioen_module(app_state, services)
    elif app_state.active_module == "fp":
        main_fp.render_fp_module(app_state, services)
    
    # Reset button in sidebar
    if st.sidebar.button("🔄 Start Opnieuw", use_container_width=True):
        app_state.reset()
        st.rerun()
    
    # Module information in sidebar
    if app_state.active_module == "fp":
        st.sidebar.markdown("""
            ### 📋 Financiële Planning Module
            
            Deze module helpt bij het opstellen van een compleet financieel plan:
            - Analyse huidige situatie
            - Pensioenplanning
            - Risicoanalyse
            - Vermogensopbouw
            - Concrete aanbevelingen
        """)
    
    # Version info
    st.markdown("---")
    st.markdown("*Veldhuis Advies Assistant - v1.0.0*")

def render_hypotheek_module(app_state, services):
    """Render the Hypotheek module interface."""
    st.title("Hypotheek Adviseur 🏠")
    
    if app_state.step == "input":
        render_input_section(services, app_state)
    elif app_state.step == "additional_questions":
        from question_recorder import render_question_recorder
        render_question_recorder(
            services['checklist_service'],
            lambda answers: handle_questions_complete(answers, app_state),
            lambda: handle_questions_skip(app_state),
            app_state.transcript
        )
    elif app_state.step == "results":
        render_results(app_state, services)

def render_pensioen_module(app_state, services):
    """Render the Pensioen module interface."""
    st.title("Pensioen Adviseur 💰")
    st.info("Deze module is momenteel in ontwikkeling. Gebruik de Hypotheek of FP module.")

def render_input_section(services, app_state):
    """Render the initial input section."""
    st.markdown("### 📝 Voeg informatie toe")
    
    # Klantprofiel upload
    st.subheader("1. Upload Klantprofiel")
    uploaded_klantprofiel = st.file_uploader(
        "Upload het klantprofiel document",
        type=["pdf", "txt", "docx"],
        key="klantprofiel_uploader"
    )
    
    if uploaded_klantprofiel:
        process_klantprofiel_upload(uploaded_klantprofiel, app_state)
    
    # Audio/transcript input
    st.subheader("2. Voeg adviesgesprek toe")
    
    tab1, tab2, tab3 = st.tabs(["🎙️ Opnemen", "📁 Uploaden", "📝 Tekst invoeren"])
    
    with tab1:
        st.write("Neem je adviesgesprek op")
        audio = services['audio_service'].record_audio()
        if audio:
            process_audio_input(audio, app_state, services)
    
    with tab2:
        st.write("Upload een audio- of tekstbestand")
        uploaded_file = st.file_uploader(
            "Kies een bestand",
            type=["txt", "wav", "mp3", "m4a"],
            key="transcript_uploader"
        )
        if uploaded_file:
            process_file_input(uploaded_file, app_state, services)
    
    with tab3:
        st.write("Voer de tekst direct in")
        transcript = st.text_area(
            "Plak of typ hier je tekst:",
            height=300,
            key="text_input",
            placeholder="Voer hier het transcript van je adviesgesprek in..."
        )
        if st.button("Analyseer", key="analyze_btn", use_container_width=True):
            process_text_input(transcript, app_state, services)

def process_klantprofiel_upload(file, app_state):
    """Process uploaded klantprofiel."""
    try:
        if file.type == "application/pdf":
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            klantprofiel_text = ""
            for page in pdf_reader.pages:
                klantprofiel_text += page.extract_text()
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            from docx import Document
            doc = Document(file)
            klantprofiel_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        else:
            klantprofiel_text = file.getvalue().decode("utf-8")
        
        app_state.set_klantprofiel(klantprofiel_text)
        st.success("✅ Klantprofiel succesvol geüpload")
        
    except Exception as e:
        st.error(f"Error bij verwerken klantprofiel: {str(e)}")

def process_audio_input(audio, app_state, services):
    """Process recorded audio input."""
    with st.spinner("Audio wordt verwerkt..."):
        transcript = services['transcription_service'].transcribe(
            audio['bytes'],
            mode="accurate",
            language="nl"
        )
        if transcript:
            start_analysis(transcript, app_state, services)

def process_file_input(file, app_state, services):
    """Process uploaded file input."""
    with st.spinner("Bestand wordt verwerkt..."):
        if file.type.startswith('audio'):
            transcript = services['transcription_service'].transcribe(
                file.getvalue(),
                mode="accurate",
                language="nl"
            )
        else:
            transcript = file.getvalue().decode("utf-8")
            
        if transcript:
            start_analysis(transcript, app_state, services)

def process_text_input(transcript, app_state, services):
    """Process directly entered text input."""
    if transcript and transcript.strip():
        start_analysis(transcript, app_state, services)
    else:
        st.error("Voer eerst tekst in om te analyseren")

def start_analysis(transcript, app_state, services):
    """Start the analysis process."""
    app_state.set_transcript(transcript)
    
    with st.spinner("Analyse wordt uitgevoerd..."):
        if app_state.active_module == "fp":
            result = services['fp_service'].process_input(transcript, app_state.klantprofiel)
        else:
            result = services['gpt_service'].analyze_initial_transcript(transcript)
        
        if result:
            app_state.set_missing_info(result.get('missing_info', {}))
            if not any(result.get('missing_info', {}).values()):
                app_state.set_analysis_complete(True)
                app_state.set_step("results")
            else:
                app_state.set_step("additional_questions")
            st.rerun()

def render_results(app_state, services):
    """Render analysis results."""
    if not app_state.result:
        with st.spinner("Eindrapport wordt gegenereerd..."):
            result = services['gpt_service'].analyze_transcript(
                app_state.transcript,
                app_state
            )
            if result:
                app_state.set_result(result)
                
    from ui_components import render_results
    render_results(app_state)

def handle_questions_complete(answers, app_state):
    """Handle completion of additional questions."""
    app_state.set_additional_info(answers)
    app_state.set_step("results")
    st.rerun()

def handle_questions_skip(app_state):
    """Handle skipping of additional questions."""
    app_state.set_step("results")
    st.rerun()

if __name__ == "__main__":
    main()