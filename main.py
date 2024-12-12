"""
File: main.py
Main application file for the AI Hypotheek/Pensioen/FP Assistent.
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
from fp_components import (
    render_fp_header, render_progress_bar, render_samenvatting,
    render_situation_comparison, render_action_points
)
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
    st.title("Advies Invoer")
    
    # Klantprofiel upload
    st.subheader("1. Upload Klantprofiel")
    uploaded_klantprofiel = st.file_uploader(
        "Upload het klantprofiel document",
        type=["pdf", "txt", "docx"],
        key="klantprofiel_uploader"
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
            key="transcript_uploader"
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
            placeholder="Voer hier het transcript van uw adviesgesprek in..."
        )
        if st.button("Analyseer", use_container_width=True):
            process_initial_input(transcript, services, app_state)

def process_initial_input(transcript, services, app_state):
    """Process the initial input and determine next steps."""
    if transcript:
        app_state.set_transcript(transcript)
        
        with st.spinner("Transcript wordt geanalyseerd..."):
            if app_state.active_module == "fp":
                # Process for FP module
                analysis = services['fp_service'].analyze_transcript(transcript)
                app_state.fp_state.update_section("samenvatting", analysis)
                app_state.set_step("fp_sections")
            else:
                # Process for Hypotheek/Pensioen
                analysis = services['gpt_service'].analyze_initial_transcript(transcript)
                if analysis:
                    app_state.set_missing_info(analysis.get('missing_info', {}))
                    if not any(analysis['missing_info'].values()):
                        app_state.set_analysis_complete(True)
                        app_state.set_step("results")
                    else:
                        app_state.set_step("additional_questions")
            st.rerun()

def render_fp_module(services, app_state):
    """Render the FP module interface."""
    if app_state.step == "input":
        render_input_section(services, app_state)
    elif app_state.step == "fp_sections":
        render_fp_header()
        
        # Show progress
        progress = app_state.fp_state.get_progress()
        render_progress_bar(progress)
        
        # Section selection
        sections = {
            "Samenvatting": "samenvatting",
            "Uitwerking Advies": "uitwerking_advies",
            "Huidige Situatie": "huidige_situatie",
            "Situatie Later": "situatie_later",
            "Situatie Overlijden": "situatie_overlijden",
            "Situatie Arbeidsongeschiktheid": "situatie_arbeidsongeschiktheid",
            "Erven en Schenken": "erven_schenken",
            "Actiepunten": "actiepunten"
        }
        
        section = st.selectbox("Selecteer sectie", list(sections.keys()))
        section_key = sections[section]
        
        # Show original transcript in expander
        with st.expander("📝 Oorspronkelijk transcript", expanded=False):
            st.write(app_state.transcript)
        
        # Audio recording for selected section
        st.subheader("🎙️ Neem uw adviesnotities op")
        
        audio = services['audio_service'].record_audio()
        if audio:
            with st.spinner("Audio wordt verwerkt..."):
                result = services['fp_service'].process_advisor_recording(
                    audio['bytes'],
                    section_key
                )
                if result:
                    app_state.fp_state.update_section(section_key, result)
                    st.success(f"Sectie {section} is bijgewerkt!")
                    st.rerun()
        
        # Generate final report button
        if app_state.fp_state.is_complete():
            if st.button("Genereer Eindrapport", use_container_width=True):
                app_state.set_step("fp_report")
                st.rerun()
                
    elif app_state.step == "fp_report":
        render_fp_header()
        report_data = services['fp_service'].generate_fp_report(app_state)
        
        # Render each section
        render_samenvatting(report_data["samenvatting"])
        st.markdown("---")
        
        for section, data in report_data.items():
            if section != "samenvatting" and section != "actiepunten":
                if section in ["situatie_later", "situatie_overlijden", "situatie_arbeidsongeschiktheid"]:
                    render_situation_comparison(
                        section.replace("_", " ").title(),
                        data["voor_advies"],
                        data["na_advies"]
                    )
                else:
                    st.header(section.replace("_", " ").title())
                    st.write(data.get("content", ""))
                    if data.get("graphs"):
                        st.plotly_chart(data["graphs"])
                st.markdown("---")
        
        render_action_points(report_data["actiepunten"])
        
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
    app_state.active_module = selected.lower()
    
    # Render appropriate module
    if app_state.active_module == "fp":
        render_fp_module(services, app_state)
    else:
        # Existing Hypotheek/Pensioen flow
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
    
    # Reset button in sidebar
    if st.sidebar.button("Start Opnieuw", use_container_width=True):
        app_state.reset()
        st.rerun()
    
    # Version info in footer
    st.markdown("---")
    st.markdown("*Veldhuis Advies Assistant - v0.0.6*")

if __name__ == "__main__":
    main()