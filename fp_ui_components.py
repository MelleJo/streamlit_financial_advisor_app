"""
File: fp_ui_components.py
UI components for the FP module.
"""

import streamlit as st
from typing import Dict, Any
import plotly.graph_objects as go

def render_section_header(title: str, icon: str, completion: float = 0):
    """Renders a section header with progress indicator."""
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.subheader(f"{icon} {title}")
    with col2:
        st.progress(completion)
        st.caption(f"{int(completion * 100)}% compleet")

def render_situation_comparison(voor: Dict, na: Dict, title: str):
    """Renders a before/after situation comparison."""
    st.subheader(title)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Situatie voor advies")
        st.write(voor.get("content", ""))
        
    with col2:
        st.markdown("### Situatie na advies")
        st.write(na.get("content", ""))
    
    # Render graph if data available
    if "years" in voor and "values" in voor:
        from fp_report_service import FPReportService
        fig = FPReportService.create_situation_graph(voor, na)
        st.plotly_chart(fig)

def render_action_points(actiepunten: Dict):
    """Renders action points section."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Actiepunten Cliënt")
        for actie in actiepunten.get("client", []):
            st.markdown(f"- {actie}")
            
    with col2:
        st.markdown("### Actiepunten Veldhuis")
        for actie in actiepunten.get("veldhuis", []):
            st.markdown(f"- {actie}")

def render_export_options(fp_state: Any):
    """Renders export options."""
    st.markdown("### 📑 Export Opties")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download als Word", use_container_width=True):
            from fp_report_service import FPReportService
            doc_buffer = FPReportService.generate_docx(fp_state)
            st.download_button(
                label="Download DOCX",
                data=doc_buffer,
                file_name="financieel_plan.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
    with col2:
        if st.button("Download als PDF", use_container_width=True):
            # PDF generation would go here
            st.info("PDF export komt binnenkort beschikbaar")