"""
File: fp_ui_components.py
Enhanced UI components for Financial Planning module
"""

import streamlit as st
from typing import Dict, Any, List
import json

def render_fp_section_header(title: str, icon: str, section_status: Dict[str, Any]):
    """Render a section header with status indicators."""
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        st.subheader(f"{icon} {title}")
    
    with col2:
        if section_status.get("complete"):
            st.success("✅ Compleet")
        elif section_status.get("in_progress"):
            st.info("🔄 In Behandeling")
        else:
            st.warning("📝 Nog Te Behandelen")

def render_fp_graph_placeholder(graph_info: Dict[str, Any]):
    """Render a professional placeholder for a graph."""
    st.markdown("""
        <style>
        .graph-placeholder {
            background: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            text-align: center;
        }
        .graph-title {
            color: #1a73e8;
            font-weight: 500;
            margin-bottom: 10px;
        }
        .graph-requirements {
            color: #6c757d;
            font-size: 0.9em;
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="graph-placeholder">
            <div class="graph-title">{graph_info['title']}</div>
            <div class="graph-requirements">
                X-as: {graph_info['data_requirements']['x_axis']}<br>
                Y-as: {graph_info['data_requirements']['y_axis']}<br>
                Series: {', '.join(graph_info['data_requirements']['series'])}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_fp_section(
    title: str,
    icon: str,
    content: Dict[str, Any],
    section_status: Dict[str, Any],
    graphs: List[Dict[str, Any]] = None
):
    """Render a complete FP section with content and graph placeholders."""
    render_fp_section_header(title, icon, section_status)
    
    if content.get("content"):
        st.markdown(content["content"])
    
    if graphs:
        st.subheader("📊 Grafieken")
        for graph in graphs:
            render_fp_graph_placeholder(graph)
    
    if section_status.get("missing_info"):
        st.warning("⚠️ Ontbrekende informatie:")
        for item in section_status["missing_info"]:
            st.markdown(f"- {item}")

def render_fp_summary(summary_data: Dict[str, Any]):
    """Render the FP summary section."""
    st.header("📋 Samenvatting Financieel Plan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Netto Besteedbaar Inkomen",
            f"€ {summary_data.get('netto_besteedbaar_inkomen', '0')}",
            help="Maandelijks besteedbaar inkomen na vaste lasten"
        )
    
    with col2:
        st.metric(
            "Benodigd Pensioeninkomen",
            f"€ {summary_data.get('benodigd_pensioen_inkomen', '0')}",
            help="Gewenst maandelijks inkomen na pensionering"
        )
    
    if summary_data.get("doelstellingen"):
        st.subheader("🎯 Financiële Doelstellingen")
        for doel in summary_data["doelstellingen"]:
            st.markdown(f"- {doel}")
    
    if summary_data.get("kernadvies"):
        st.info(summary_data["kernadvies"])

def render_fp_risk_analysis(risk_data: Dict[str, Any]):
    """Render the risk analysis section."""
    st.header("⚠️ Risico Analyse")
    
    tabs = st.tabs(["💔 Overlijden", "🏥 Arbeidsongeschiktheid", "💼 Werkloosheid"])
    
    with tabs[0]:
        if risk_data.get("overlijden"):
            st.markdown(risk_data["overlijden"]["analysis"])
            if risk_data["overlijden"].get("graph"):
                render_fp_graph_placeholder(risk_data["overlijden"]["graph"])
    
    with tabs[1]:
        if risk_data.get("arbeidsongeschiktheid"):
            st.markdown(risk_data["arbeidsongeschiktheid"]["analysis"])
            if risk_data["arbeidsongeschiktheid"].get("graph"):
                render_fp_graph_placeholder(risk_data["arbeidsongeschiktheid"]["graph"])
    
    with tabs[2]:
        if risk_data.get("werkloosheid"):
            st.markdown(risk_data["werkloosheid"]["analysis"])
            if risk_data["werkloosheid"].get("graph"):
                render_fp_graph_placeholder(risk_data["werkloosheid"]["graph"])

def render_fp_action_points(action_points: Dict[str, List[str]]):
    """Render the action points section."""
    st.header("✅ Actiepunten")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Acties Client")
        if action_points.get("client"):
            for action in action_points["client"]:
                st.markdown(f"- {action}")
        else:
            st.info("Geen actiepunten gedefinieerd")
    
    with col2:
        st.subheader("🏢 Acties Veldhuis")
        if action_points.get("veldhuis"):
            for action in action_points["veldhuis"]:
                st.markdown(f"- {action}")
        else:
            st.info("Geen actiepunten gedefinieerd")

def render_fp_export_options(fp_data: Dict[str, Any]):
    """Render export options for the FP report."""
    st.header("📑 Rapport Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Download als Word", key="word_export", use_container_width=True):
            from fp_report_service import generate_word_report
            doc_buffer = generate_word_report(fp_data)
            st.download_button(
                label="⬇️ Download Word Document",
                data=doc_buffer,
                file_name="financieel_plan.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    
    with col2:
        if st.button("📊 Download als PDF", key="pdf_export", use_container_width=True):
            from fp_report_service import generate_pdf_report
            pdf_buffer = generate_pdf_report(fp_data)
            st.download_button(
                label="⬇️ Download PDF Document",
                data=pdf_buffer,
                file_name="financieel_plan.pdf",
                mime="application/pdf"
            )

def render_fp_progress(progress_data: Dict[str, Any]):
    """Render progress indicators for FP report completion."""
    st.sidebar.header("📊 Voortgang Rapport")
    
    total_sections = len(progress_data["sections"])
    completed_sections = sum(1 for s in progress_data["sections"].values() if s.get("complete"))
    
    progress = completed_sections / total_sections if total_sections > 0 else 0
    st.sidebar.progress(progress)
    
    st.sidebar.markdown(f"**Compleet:** {completed_sections}/{total_sections} secties")
    
    if progress_data.get("missing_info"):
        st.sidebar.markdown("### ⚠️ Nog te behandelen")
        for section, items in progress_data["missing_info"].items():
            with st.sidebar.expander(section):
                for item in items:
                    st.markdown(f"- {item}")

def render_fp_qa_history(qa_history: List[Dict[str, Any]]):
    """Render the Q&A history for the FP session."""
    if not qa_history:
        return
    
    with st.expander("💬 Vraag & Antwoord Geschiedenis"):
        for qa in qa_history:
            st.markdown("""
                <div style="
                    background-color: #f8f9fa;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #1a73e8;
                ">
                    <p style="color: #1a73e8; margin: 0;">
                        <strong>Vraag:</strong> {question}
                    </p>
                    <p style="color: #666; font-style: italic; margin: 5px 0;">
                        Context: {context}
                    </p>
                    <p style="margin: 0;">
                        <strong>Antwoord:</strong> {answer}
                    </p>
                </div>
            """.format(
                question=qa.get("question", ""),
                context=qa.get("context", ""),
                answer=qa.get("answer", "")
            ), unsafe_allow_html=True)