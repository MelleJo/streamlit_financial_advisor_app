import streamlit as st
from docx import Document
from io import BytesIO
import json
import logging
from definitions import MORTGAGE_DEFINITIONS, improve_explanation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_custom_css():
    st.markdown("""
        <style>
        .text-paragraph {
            line-height: 1.8;
            margin-bottom: 1.25em;
            color: #1f2937;
            font-size: 1rem;
        }

        .standard-explanations {
            background: #f8fafc;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            border: 1px solid #e2e8f0;
        }

        .qa-history {
            background: #f8fafc;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid #e2e8f0;
        }

        .qa-pair {
            background: white;
            padding: 1rem;
            border-radius: 6px;
            margin: 0.5rem 0;
            border: 1px solid #e5e7eb;
        }

        .qa-context {
            color: #6b7280;
            font-size: 0.9em;
            font-style: italic;
            margin-bottom: 0.5rem;
        }

        .qa-question {
            color: #1a73e8;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .qa-answer {
            color: #374151;
        }

        .explanation-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            padding: 1.25rem;
            border-radius: 12px;
            border: 1px solid rgba(226, 232, 240, 0.8);
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        </style>
    """, unsafe_allow_html=True)

def render_qa_history(qa_history, section):
    if not qa_history:
        return
    
    relevant_qa = [qa for qa in qa_history if qa.get('category') == section]
    if not relevant_qa:
        return
    
    st.markdown("""
        <div class="qa-history">
            <h4>Aanvullende informatie uit het gesprek:</h4>
    """, unsafe_allow_html=True)
    
    for qa in relevant_qa:
        st.markdown(f"""
            <div class="qa-pair">
                <div class="qa-context">{qa.get('context', '')}</div>
                <div class="qa-question">Vraag: {qa.get('question', '')}</div>
                <div class="qa-answer">Antwoord: {qa.get('answer', '')}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_standard_explanations(section: str, current_content: str) -> str:
    """Renders standard explanation options for a section."""
    # Initialize OpenAI client if needed
    if 'openai_client' not in st.session_state:
        try:
            from openai import OpenAI
            st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        except Exception as e:
            st.error(f"Error initializing OpenAI client: {str(e)}")
            return current_content

    standard_explanations = {
        "adviesmotivatie_leningdeel": {
            "Hypotheekvormen": """Een hypotheek is een lening met een woning als onderpand. Er zijn verschillende hypotheekvormen waaruit u kunt kiezen. De meest voorkomende vormen zijn de annuïteitenhypotheek en de lineaire hypotheek.""",
            "NHG-voorwaarden": """De Nationale Hypotheek Garantie (NHG) is een garantie op hypotheken. Met NHG bent u verzekerd van een verantwoorde hypotheek die aansluit op uw situatie. Bovendien kunt u met NHG profiteren van een rentevoordeel.""",
            "Rentevaste periodes": """De rentevaste periode is de periode waarin uw hypotheekrente gelijk blijft. Hoe langer deze periode, hoe meer zekerheid u heeft over uw maandlasten.""",
            "Maandlasten berekening": """De maandlasten van uw hypotheek bestaan uit verschillende componenten: rente, aflossing (bij annuïtair of lineair), en eventuele verzekeringspremies."""
        }
    }

    if section not in standard_explanations:
        return current_content

    col1, col2 = st.columns(2)
    updated_content = current_content

    for idx, (label, explanation) in enumerate(standard_explanations[section].items()):
        with col1 if idx % 2 == 0 else col2:
            if st.button(f"➕ {label}", key=f"{section}_{idx}", use_container_width=True):
                try:
                    # Use improve_explanation to enhance the text
                    with st.spinner(f"Uitleg over {label} wordt toegevoegd..."):
                        improved = improve_explanation(
                            label,
                            explanation,
                            updated_content,
                            st.session_state.openai_client
                        )
                        if improved:
                            updated_content = improved
                except Exception as e:
                    st.error(f"Fout bij het toevoegen van uitleg: {str(e)}")

    return updated_content

def render_results(app_state):
    st.title("Analyse Resultaten")
    
    if not app_state.transcript or not app_state.transcript.strip():
        st.warning("⚠️ Geen transcript beschikbaar. Maak eerst een opname of voer een transcript in.")
        if st.button("↩️ Terug naar invoer"):
            app_state.reset()
            st.rerun()
        return
    
    if not app_state.result or not any(content.strip() for content in app_state.result.values()):
        st.warning("⚠️ Geen analyse resultaten beschikbaar.")
        if st.button("🔄 Opnieuw analyseren"):
            app_state.reset()
            st.rerun()
        return

    with st.expander("📝 Oorspronkelijk transcript", expanded=False):
        st.markdown(f"```{app_state.transcript}```")

    for section, content in app_state.result.items():
        if not content or not content.strip():
            continue
            
        with st.expander(section.replace("_", " ").capitalize(), expanded=True):
            paragraphs = [p for p in content.split('\n') if p.strip()]
            for paragraph in paragraphs:
                st.markdown(f'<div class="text-paragraph">{paragraph}</div>', unsafe_allow_html=True)
            
            render_qa_history(app_state.structured_qa_history, section.replace("adviesmotivatie_", ""))
            
            updated_content = render_standard_explanations(section, content)
            if updated_content != content:
                app_state.result[section] = updated_content
                st.rerun()

    if any(content.strip() for content in app_state.result.values()):
        st.markdown("### 📑 Exporteer Resultaten")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📎 Exporteer als Word", use_container_width=True):
                export_to_docx(app_state)
                
        with col2:
            if st.button("🔄 Nieuwe Analyse", use_container_width=True):
                app_state.reset()
                st.rerun()

def export_to_docx(app_state):
    doc = Document()
    doc.add_heading('Hypotheek Advies Analyse', 0)
    doc.add_paragraph(f'Gegenereerd op: {st.session_state.get("current_date", "")}')

    doc.add_heading('Transcript', level=1)
    doc.add_paragraph(app_state.transcript)

    for section, content in app_state.result.items():
        if not content.strip():
            continue
            
        doc.add_heading(section.replace("_", " ").capitalize(), level=1)
        
        for line in content.split('\n'):
            if line.strip():
                if line.strip().startswith('*') and line.strip().endswith('*'):
                    doc.add_paragraph(line.strip()[1:-1], style='Heading 2')
                else:
                    doc.add_paragraph(line)

        section_qa = [qa for qa in app_state.structured_qa_history 
                     if qa.get('category') == section.replace("adviesmotivatie_", "")]
        
        if section_qa:
            doc.add_heading('Aanvullende Informatie', level=2)
            for qa in section_qa:
                p = doc.add_paragraph()
                p.add_run('Context: ').bold()
                p.add_run(qa.get('context', ''))
                p = doc.add_paragraph()
                p.add_run('Vraag: ').bold()
                p.add_run(qa.get('question', ''))
                p = doc.add_paragraph()
                p.add_run('Antwoord: ').bold()
                p.add_run(qa.get('answer', ''))
                doc.add_paragraph()

    docx_buffer = BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)
    
    st.download_button(
        label="⬇️ Download Word Document",
        data=docx_buffer,
        file_name="hypotheek_advies_analyse.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )