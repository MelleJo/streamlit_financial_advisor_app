"""
File: ui_components.py
Provides all UI components and styling for the AI Hypotheek Assistent.
"""

import streamlit as st
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from docx import Document
from io import BytesIO
import logging
import re
from definitions import MORTGAGE_DEFINITIONS, improve_explanation

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_custom_css():
    st.markdown("""
    <style>
    .term-highlight {
        background: linear-gradient(120deg, #E8F0FE 0%, #d2e3fc 100%);
        border-radius: 4px;
        padding: 2px 6px;
        margin: 0 2px;
        cursor: pointer;
        display: inline-block;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        color: #1a73e8;
        text-decoration: none;
        font-weight: 500;
    }
    
    .term-highlight:hover {
        background: linear-gradient(120deg, #d2e3fc 0%, #c2d9fc 100%);
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    .explanation-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        animation: slideIn 0.3s ease-out;
    }

    .explanation-title {
        color: #1a73e8;
        margin-bottom: 0.75rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-bottom: 2px solid rgba(26, 115, 232, 0.1);
        padding-bottom: 0.5rem;
    }

    .explanation-content {
        color: #374151;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    .text-paragraph {
        line-height: 1.8;
        margin-bottom: 1.25em;
        color: #1f2937;
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def render_results(app_state):
    """Renders the analysis results with clickable terms and definitions."""
    st.title("Analyse Resultaten")
    
    if not app_state.result:
        st.warning("Er zijn geen resultaten beschikbaar.")
        return
    
    # Initialize session state for term selection
    if 'selected_term' not in st.session_state:
        st.session_state.selected_term = None
    if 'selected_section' not in st.session_state:
        st.session_state.selected_section = None
    if 'enhanced_texts' not in st.session_state:
        st.session_state.enhanced_texts = {}

    # Process each section
    for section, content in app_state.result.items():
        with st.expander(section.replace("_", " ").capitalize(), expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Process text paragraph by paragraph
                for paragraph in content.split('\n'):
                    if not paragraph.strip():
                        continue
                    
                    # Find all mortgage terms in the paragraph
                    terms_in_paragraph = []
                    for term in MORTGAGE_DEFINITIONS.keys():
                        if re.search(r'\b' + re.escape(term) + r'\b', paragraph, re.IGNORECASE):
                            terms_in_paragraph.append(term)
                    
                    # Display paragraph text
                    st.markdown(f'<div class="text-paragraph">{paragraph}</div>', unsafe_allow_html=True)
                    
                    # Add clickable buttons for terms found in the paragraph
                    if terms_in_paragraph:
                        cols = st.columns(min(3, len(terms_in_paragraph)))
                        for idx, term in enumerate(terms_in_paragraph):
                            with cols[idx % 3]:
                                if st.button(f"📚 {term}", key=f"{section}_{term}_{idx}"):
                                    st.session_state.selected_term = term
                                    st.session_state.selected_section = section
                                    st.rerun()
            
            with col2:
                # Show definition if term is selected for this section
                if (st.session_state.selected_term and 
                    st.session_state.selected_section == section):
                    
                    st.markdown(f"""
                        <div class="explanation-card">
                            <div class="explanation-title">
                                📚 {st.session_state.selected_term}
                            </div>
                            <div class="explanation-content">
                                {MORTGAGE_DEFINITIONS[st.session_state.selected_term].replace('\n', '<br>')}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(
                        "➕ Voeg uitleg toe", 
                        type="primary",
                        use_container_width=True,
                        key=f"add_{section}_{st.session_state.selected_term}"
                    ):
                        enhanced_text = improve_explanation(
                            st.session_state.selected_term,
                            MORTGAGE_DEFINITIONS[st.session_state.selected_term],
                            content,
                            st.session_state.openai_client
                        )
                        
                        if enhanced_text:
                            st.session_state.enhanced_texts[section] = enhanced_text
                            if section in app_state.result:
                                app_state.result[section] = enhanced_text
                                st.rerun()

    if st.button("Exporteer als Word-document", use_container_width=True):
        export_to_docx(app_state.result)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Terug naar Start", use_container_width=True):
            app_state.set_step("choose_method")
    with col2:
        if st.button("Nieuwe Analyse", use_container_width=True):
            app_state.reset()

def export_to_docx(result):
    doc = Document()
    doc.add_heading('Analyse Resultaten', 0)

    for section, content in result.items():
        doc.add_heading(section.replace("_", " ").capitalize(), level=1)
        for line in content.split('\n'):
            if line.strip().startswith('**') and line.strip().endswith('**'):
                doc.add_paragraph(line.strip()[2:-2], style='Heading 2')
            else:
                doc.add_paragraph(line)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    
    st.download_button(
        label="Download Word Document",
        data=bio.getvalue(),
        file_name="analyse_resultaten.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
