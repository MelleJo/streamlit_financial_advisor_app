import streamlit as st
import logging
import asyncio
from typing import Dict, Any
from fp_integration_service import FPIntegrationService
from fp_ui_components import (
    render_fp_section, render_fp_summary, render_fp_risk_analysis,
    render_fp_action_points, render_fp_export_options, render_fp_progress
)
from audio_service import AudioService
from transcription_service import TranscriptionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_fp_module(app_state, services):
    """Main render function for FP module."""
    st.title("Financiële Planning Adviseur 📋")
    
    # Initialize services if not already done
    if 'fp_integration_service' not in st.session_state:
        st.session_state.fp_integration_service = FPIntegrationService(api_key=st.secrets["OPENAI_API_KEY"])
    
    fp_service = st.session_state.fp_integration_service
    
    # Show different views based on step
    if app_state.step == "input":
        render_input_section(app_state, services)
    elif app_state.step == "analysis":
        asyncio.run(render_analysis_section(app_state, fp_service))
    elif app_state.step == "qa":
        render_qa_section(app_state, fp_service)
    elif app_state.step == "report":
        render_report_section(app_state, fp_service)

def render_input_section(app_state, services):
    """Render the initial input section."""
    st.markdown("""
        ### 📝 Voeg informatie toe
        Upload een klantprofiel en voeg het adviesgesprek toe via een opname, 
        bestand of tekst.
    """)
    
    # Klantprofiel upload
    st.subheader("1. Upload Klantprofiel")
    uploaded_klantprofiel = st.file_uploader(
        "Upload het klantprofiel document",
        type=["pdf", "txt", "docx"],
        key="fp_klantprofiel_uploader"
    )
    
    if uploaded_klantprofiel:
        try:
            if uploaded_klantprofiel.type == "application/pdf":
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_klantprofiel)
                klantprofiel_text = ""
                for page in pdf_reader.pages:
                    klantprofiel_text += page.extract_text()
            else:
                klantprofiel_text = uploaded_klantprofiel.getvalue().decode("utf-8")
            
            app_state.fp_state.klantprofiel = klantprofiel_text
            st.success("✅ Klantprofiel succesvol geüpload")
            
        except Exception as e:
            st.error(f"Error bij verwerken klantprofiel: {str(e)}")
    
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
            key="fp_transcript_uploader"
        )
        if uploaded_file:
            process_file_input(uploaded_file, app_state, services)
    
    with tab3:
        st.write("Voer de tekst direct in")
        transcript = st.text_area(
            "Plak of typ hier je tekst:",
            height=300,
            key="fp_text_input",
            placeholder="Voer hier het transcript van je adviesgesprek in..."
        )
        if st.button("Analyseer", key="fp_analyze_btn", use_container_width=True):
            process_text_input(transcript, app_state, services)

def process_audio_input(audio, app_state, services):
    """Process recorded audio input."""
    with st.spinner("Audio wordt verwerkt..."):
        transcript = services['transcription_service'].transcribe(
            audio['bytes'],
            mode="accurate",
            language="nl"
        )
        if transcript:
            start_analysis(transcript, app_state)

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
            start_analysis(transcript, app_state)

def process_text_input(transcript, app_state, services):
    """Process directly entered text input."""
    if transcript and transcript.strip():
        start_analysis(transcript, app_state)
    else:
        st.error("Voer eerst tekst in om te analyseren")

def start_analysis(transcript, app_state):
    """Start the analysis process with the transcript."""
    app_state.fp_state.transcript = transcript
    app_state.step = "analysis"
    st.rerun()

async def render_analysis_section(app_state, fp_service):
    """Render the analysis section."""
    try:
        with st.spinner("Analyse wordt uitgevoerd..."):
            result = await fp_service.process_input(
                app_state.fp_state.transcript,
                app_state.fp_state.klantprofiel
            )
        
        if result["status"] == "success":
            st.success("✅ Analyse compleet")
            
            if result.get("missing_info"):
                app_state.step = "qa"
                st.warning("Er ontbreekt nog enkele informatie")
                st.rerun()
            else:
                app_state.step = "report"
                st.rerun()
        else:
            st.error("Er is een fout opgetreden bij de analyse")
            
    except Exception as e:
        st.error(f"Error tijdens analyse: {str(e)}")

def render_qa_section(app_state, fp_service):
    """Render the Q&A section for missing information."""
    st.header("📝 Aanvullende Informatie Nodig")
    
    with st.expander("📄 Oorspronkelijk transcript", expanded=False):
        st.write(app_state.fp_state.transcript)
    
    qa_tabs = st.tabs(["❓ Vragen", "📝 Antwoorden", "📊 Voortgang"])
    
    with qa_tabs[0]:
        questions = fp_service.get_next_questions()
        if not questions:
            st.success("✅ Alle benodigde informatie is verzameld")
            app_state.step = "report"
            st.rerun()
        
        for q in questions:
            st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin: 10px 0;'>
                    <p style='color: #1f2937; margin-bottom: 5px;'><strong>{q['question']}</strong></p>
                    <p style='color: #6b7280; font-style: italic; margin: 0;'>{q['context']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    with qa_tabs[1]:
        # Audio recording for answers
        st.write("🎙️ Neem je antwoord op")
        audio = fp_service.audio_service.record_audio()
        if audio:
            asyncio.run(process_qa_audio(audio, app_state, fp_service))
    
    with qa_tabs[2]:
        render_fp_progress(fp_service.get_progress())

async def process_qa_audio(audio, app_state, fp_service):
    """Process recorded audio answers."""
    with st.spinner("Antwoord wordt verwerkt..."):
        transcript = fp_service.transcription_service.transcribe(
            audio['bytes'],
            mode="accurate",
            language="nl"
        )
        if transcript:
            result = await fp_service.process_qa_response(transcript)
            if result.get("is_complete"):
                st.success("✅ Alle informatie compleet")
                app_state.step = "report"
                st.rerun()
            else:
                st.rerun()

def render_report_section(app_state, fp_service):
    """Render the final report section."""
    st.header("📊 Financieel Plan Rapport")
    
    try:
        with st.spinner("Rapport wordt gegenereerd..."):
            report = asyncio.run(fp_service.generate_final_report())
        
        if report["status"] == "success":
            # Render summary
            render_fp_summary(report["report"]["samenvatting"])
            
            # Render each section
            sections = {
                "Huidige Situatie": "📈",
                "Pensioen": "👴",
                "Risico Analyse": "⚠️",
                "Vermogen": "💰",
                "Actiepunten": "✅"
            }
            
            for title, icon in sections.items():
                key = title.lower().replace(" ", "_")
                if key in report["report"]:
                    render_fp_section(
                        title,
                        icon,
                        report["report"][key],
                        fp_service.get_section_status(key),
                        report["report"].get("graphs", {}).get(key)
                    )
            
            # Render export options
            render_fp_export_options(report["report"])
            
        else:
            st.error("Er is een fout opgetreden bij het genereren van het rapport")
            
    except Exception as e:
        st.error(f"Error tijdens rapport generatie: {str(e)}")

def initialize_fp_state(app_state):
    """Initialize or reset FP state."""
    app_state.fp_state.reset()
    app_state.step = "input"
