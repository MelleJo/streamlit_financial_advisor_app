"""
File: main.py
Main application file for the Veldhuis Advies Assistant.
"""

import streamlit as st
from streamlit_option_menu import option_menu
from transcription_service import TranscriptionService
from gpt_service import GPTService
from question_recorder import render_question_recorder
import ui_components as ui
from app_state import AppState
from openai import OpenAI
from audio_service import AudioService
from checklist_analysis_service import ChecklistAnalysisService
from fp_service import FPService

def initialize_services():
    """Initialize all required services."""
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("OpenAI API key is required. Please add it to your secrets.")
        st.stop()

    api_key = st.secrets["OPENAI_API_KEY"]
    
    return {
        'gpt_service': GPTService(api_key=api_key),
        'audio_service': AudioService(),
        'transcription_service': TranscriptionService(),
        'checklist_service': ChecklistAnalysisService(api_key=api_key),
        'fp_service': FPService(api_key=api_key)
    }

def render_input_section(services, app_state):
    """Render the initial input section with multiple input options."""
    module_titles = {
        "hypotheek": "Hypotheek Advies Invoer",
        "pensioen": "Pensioen Advies Invoer",
        "fp": "Financiële Planning Invoer"
    }
    st.title(module_titles.get(app_state.active_module, "Advies Invoer"))
    
    # Klantprofiel upload
    st.subheader("1. Upload Klantprofiel")
    uploaded_klantprofiel = st.file_uploader(
        "Upload het klantprofiel document",
        type=["pdf", "txt", "docx"],
        key=f"klantprofiel_uploader_{app_state.active_module}"
    )
    
    if uploaded_klantprofiel:
        try:
            if uploaded_klantprofiel.type == "application/pdf":
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_klantprofiel)
                klantprofiel_text = ""
                for page in pdf_reader.pages:
                    klantprofiel_text += page.extract_text()
            elif uploaded_klantprofiel.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                from docx import Document
                doc = Document(uploaded_klantprofiel)
                klantprofiel_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            else:
                klantprofiel_text = uploaded_klantprofiel.getvalue().decode("utf-8")
            
            app_state.set_klantprofiel(klantprofiel_text)
            st.success("✅ Klantprofiel succesvol geüpload")
        except Exception as e:
            st.error(f"Error bij verwerken klantprofiel: {str(e)}")
    
    st.subheader("2. Voeg adviesgesprek toe")
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
            type=["txt", "docx", "wav", "mp3", "m4a"],
            key=f"transcript_uploader_{app_state.active_module}"
        )
        if uploaded_file:
            with st.spinner("Bestand wordt verwerkt..."):
                if uploaded_file.type.startswith('audio'):
                    transcript = services['transcription_service'].transcribe(
                        uploaded_file.getvalue(),
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
            key=f"text_input_{app_state.active_module}",
            placeholder="Voer hier het transcript van uw adviesgesprek in..."
        )
        if st.button("Analyseer", key=f"analyze_btn_{app_state.active_module}", use_container_width=True):
            process_initial_input(transcript, services, app_state)

def process_initial_input(transcript, services, app_state):
    """Process the initial input and determine next steps."""
    if transcript:
        app_state.set_transcript(transcript)
        
        with st.spinner("Transcript wordt geanalyseerd..."):
            if app_state.active_module == "fp":
                analysis = services['fp_service'].analyze_transcript(transcript)
                app_state.fp_state.update_section("samenvatting", analysis)
                app_state.set_step("fp_sections")
            else:
                analysis = services['gpt_service'].analyze_initial_transcript(transcript)
                if analysis:
                    app_state.set_missing_info(analysis.get('missing_info', {}))
                    if not any(analysis['missing_info'].values()):
                        app_state.set_analysis_complete(True)
                        app_state.set_step("results")
                    else:
                        app_state.set_step("additional_questions")
            st.rerun()

def handle_questions_complete(answers, app_state):
    """Handle completion of additional questions."""
    app_state.set_additional_info(answers)
    app_state.set_step("results")
    st.rerun()

def handle_questions_skip(app_state):
    """Handle skipping of additional questions."""
    app_state.set_step("results")
    st.rerun()

def render_hypotheek_module(app_state, services):
    """Render the Hypotheek module interface."""
    st.title("Hypotheek Adviseur 🏠")
    
    if app_state.step == "input":
        render_input_section(services, app_state)
    elif app_state.step == "additional_questions":
        with st.expander("📝 Oorspronkelijk transcript"):
            st.write(app_state.transcript)
        render_question_recorder(
            services['transcription_service'],
            services['checklist_service'],
            lambda answers: handle_questions_complete(answers, app_state),
            lambda: handle_questions_skip(app_state),
            app_state.transcript
        )
    elif app_state.step == "results":
        if not app_state.result:
            with st.spinner("Eindrapport wordt gegenereerd..."):
                result = services['gpt_service'].analyze_transcript(
                    app_state.transcript,
                    app_state
                )
                if result:
                    app_state.set_result(result)
        ui.render_results(app_state)

def render_pensioen_module(app_state, services):
    """Render the Pensioen module interface."""
    st.title("Pensioen Adviseur 💰")
    
    # Temporary "under construction" message
    st.markdown("""
        ### Module in ontwikkeling
        
        De Pensioen Adviseur module is momenteel in ontwikkeling. Hier komt binnenkort:
        
        - Geautomatiseerde pensioenanalyse
        - Berekening van uw pensioengat
        - Scenario analyses voor verschillende pensioenleeftijden
        - Advies over aanvullende pensioenopbouw
        - Integratie met bestaande pensioenvoorzieningen
        
        We werken hard om deze functionaliteit zo snel mogelijk beschikbaar te maken.
        
        *Gebruik voorlopig de Hypotheek Adviseur of Financiële Planning modules.*
        """)
    
    # Progress indicator
    st.progress(0.4)
    st.caption("🔨 Module gereed: 40%")

def render_fp_module(app_state, services):
    """Render the Financial Planning module interface."""
    st.title("Financiële Planning Adviseur 📋")
    
    if app_state.step == "input":
        # Introduction text specific to FP
        st.markdown("""
            ### Welkom bij de Financiële Planning Module
            
            Deze module helpt u bij het opstellen van een compleet financieel plan, inclusief:
            - Analyse van uw huidige financiële situatie
            - Planning voor verschillende levensfases
            - Scenario-analyses voor pensioen, overlijden en arbeidsongeschiktheid
            - Advies over vermogensopbouw en -beheer
            
            Begin met het uploaden van uw klantprofiel en een opname van het adviesgesprek.
            """)
        render_input_section(services, app_state)
            
    elif app_state.step == "fp_sections":
        # Show progress of FP report
        progress = app_state.fp_state.get_progress()
        st.progress(progress / 100)
        st.write(f"Rapport voortgang: {progress:.0f}%")
        
        # Section selection
        sections = {
            "Samenvatting": ("samenvatting", "📋"),
            "Uitwerking Advies": ("uitwerking_advies", "📊"),
            "Huidige Situatie": ("huidige_situatie", "📈"),
            "Situatie Later": ("situatie_later", "🎯"),
            "Situatie Overlijden": ("situatie_overlijden", "💼"),
            "Situatie Arbeidsongeschiktheid": ("situatie_arbeidsongeschiktheid", "🏥"),
            "Erven en Schenken": ("erven_schenken", "🎁"),
            "Actiepunten": ("actiepunten", "✅")
        }
        
        # Display original transcript in expander
        with st.expander("📝 Oorspronkelijk transcript", expanded=False):
            st.write(app_state.transcript)
        
        # Section tabs
        tabs = st.tabs([f"{icon} {name}" for name, (key, icon) in sections.items()])
        
        for idx, (section_name, (section_key, icon)) in enumerate(sections.items()):
            with tabs[idx]:
                st.subheader(f"{icon} {section_name}")
                
                # Show current section content if it exists
                section_data = getattr(app_state.fp_state, section_key, None)
                if section_data and section_data.get("content"):
                    st.write(section_data["content"])
                    if section_data.get("graphs"):
                        st.plotly_chart(section_data["graphs"])
                
                # Audio recording for this section
                st.markdown("### 🎙️ Neem uw adviesnotities op")
                audio = services['audio_service'].record_audio()
                
                if audio:
                    with st.spinner("Audio wordt verwerkt..."):
                        result = services['fp_service'].process_advisor_recording(
                            audio['bytes'],
                            section_key
                        )
                        if result:
                            app_state.fp_state.update_section(section_key, result)
                            st.success(f"Sectie {section_name} is bijgewerkt!")
                            st.rerun()
        
        # Generate final report button
        if app_state.fp_state.is_complete():
            if st.button("Genereer Eindrapport", use_container_width=True):
                app_state.set_step("fp_report")
                st.rerun()
                
    elif app_state.step == "fp_report":
        report_data = services['fp_service'].generate_fp_report(app_state)
        
        # Export options
        st.markdown("### 📑 Export Opties")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download als PDF", use_container_width=True):
                ui.export_to_pdf(report_data)
        with col2:
            if st.button("Download als Word", use_container_width=True):
                ui.export_to_docx(report_data)

def main():
    """Main application flow."""
    # Page config
    st.set_page_config(page_title="Veldhuis Advies Assistant", page_icon="🏠", layout="wide")
    ui.apply_custom_css()
    
    # Initialize services and state
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
        app_state.active_module = selected.lower()
        app_state.reset()  # Reset state when switching modules
        st.rerun()
    
    # Render appropriate module
    if app_state.active_module == "hypotheek":
        render_hypotheek_module(app_state, services)
    elif app_state.active_module == "pensioen":
        render_pensioen_module(app_state, services)
    elif app_state.active_module == "fp":
        render_fp_module(app_state, services)
    
    # Reset button in sidebar
    if st.sidebar.button("Start Opnieuw", use_container_width=True):
        app_state.reset()
        st.rerun()
    
    # Version info in footer
    st.markdown("---")
    st.markdown("*Veldhuis Advies Assistant - v0.0.6*")

if __name__ == "__main__":
    main()