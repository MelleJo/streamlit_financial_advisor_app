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

    .standard-explanations {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        border: 1px solid #e2e8f0;
    }

    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }

    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

def render_loading_overlay():
    st.markdown("""
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div style="margin-left: 1rem;">Bezig met verwerken...</div>
        </div>
    """, unsafe_allow_html=True)

def render_results(app_state):
    """Renders the analysis results with clickable terms and definitions."""
    st.title("Analyse Resultaten")
    
    if not app_state.result:
        st.warning("Er zijn geen resultaten beschikbaar.")
        return
    
    # Initialize session state
    if 'selected_term' not in st.session_state:
        st.session_state.selected_term = None
    if 'selected_section' not in st.session_state:
        st.session_state.selected_section = None
    if 'is_loading' not in st.session_state:
        st.session_state.is_loading = False

    # Standard explanation options per section
    standard_explanations = {
        "adviesmotivatie_leningdeel": [
            "Hypotheekvormen",
            "Rentevaste periodes",
            "NHG-voorwaarden",
            "Maandlasten berekening"
        ],
        "adviesmotivatie_werkloosheid": [
            "WW-uitkering",
            "Woonlastenverzekering",
            "Werkloosheidsrisico's",
            "Financiële buffer"
        ],
        "adviesmotivatie_aow": [
            "Pensioenopbouw",
            "AOW-leeftijd",
            "Hypotheek na pensionering",
            "Vermogensplanning"
        ]
    }

    # Show loading overlay if processing
    if st.session_state.is_loading:
        render_loading_overlay()

    # Process each section
    for section, content in app_state.result.items():
        with st.expander(section.replace("_", " ").capitalize(), expanded=True):
            # Display the content
            paragraphs = [p for p in content.split('\n') if p.strip()]
            for para_idx, paragraph in enumerate(paragraphs):
                st.markdown(f'<div class="text-paragraph">{paragraph}</div>', unsafe_allow_html=True)
            
            # Standard explanations section
            st.markdown("""
                <div class="standard-explanations">
                    <h4>Voeg standaard uitleg toe:</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # Create columns for explanation options
            cols = st.columns(2)
            for idx, explanation in enumerate(standard_explanations[section]):
                with cols[idx % 2]:
                    if st.button(
                        f"➕ {explanation}",
                        key=f"{section}_exp_{idx}",
                        use_container_width=True
                    ):
                        st.session_state.is_loading = True
                        enhanced_text = improve_explanation(
                            explanation,
                            f"Standaard uitleg over {explanation}",
                            content,
                            st.session_state.openai_client
                        )
                        if enhanced_text:
                            app_state.result[section] = enhanced_text
                        st.session_state.is_loading = False
                        st.rerun()

    # Export and navigation buttons
    if st.button("Exporteer als Word-document", use_container_width=True):
        export_to_docx(app_state.result)

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
