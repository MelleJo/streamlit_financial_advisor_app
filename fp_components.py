"""
File: fp_components.py
Streamlit UI components for Financial Planning sections
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List

def render_fp_header():
    """Render the FP report header"""
    st.title("Financiële Planning Rapport")
    st.markdown("---")

def render_progress_bar(progress: float):
    """Render progress bar for report completion"""
    st.progress(progress / 100)
    st.write(f"Rapport voortgang: {progress:.0f}%")

def render_samenvatting(data: Dict):
    """Render the summary section"""
    st.header("📋 Samenvatting")
    
    if data.get("netto_besteedbaar_inkomen"):
        st.markdown(f"""
        **Netto besteedbaar inkomen:** €{data['netto_besteedbaar_inkomen']}
        """)
    
    if data.get("hoofdpunten"):
        st.subheader("Hoofdpunten")
        for punt in data["hoofdpunten"]:
            st.markdown(f"- {punt}")
    
    if data.get("kernadvies"):
        st.subheader("Kernadvies")
        st.write(data["kernadvies"])

def render_situation_comparison(title: str, voor_data: Dict, na_data: Dict):
    """Render before/after situation comparison"""
    st.header(title)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Situatie voor advies")
        if voor_data.get("graph"):
            st.plotly_chart(voor_data["graph"])
        st.write(voor_data.get("content", ""))
        
    with col2:
        st.subheader("Situatie na advies")
        if na_data.get("graph"):
            st.plotly_chart(na_data["graph"])
        st.write(na_data.get("content", ""))

def render_action_points(actiepunten: Dict):
    """Render action points section"""
    st.header("✅ Actiepunten")
    
    if actiepunten.get("client"):
        st.subheader("Actiepunten cliënt")
        for actie in actiepunten["client"]:
            st.markdown(f"- {actie}")
    
    if actiepunten.get("veldhuis"):
        st.subheader("Actiepunten Veldhuis Advies")
        for actie in actiepunten["veldhuis"]:
            st.markdown(f"- {actie}")

def create_line_chart(data: List[Dict], title: str) -> go.Figure:
    """Create a line chart using plotly"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[d["jaar"] for d in data],
        y=[d["waarde"] for d in data],
        mode='lines+markers',
        name='Verloop'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Jaar",
        yaxis_title="Waarde (€)",
        showlegend=True
    )
    
    return fig

def render_fp_section(title: str, icon: str, content: Dict):
    """Render a standard FP section"""
    st.header(f"{icon} {title}")
    
    if content.get("graph"):
        st.plotly_chart(content["graph"])
    
    if content.get("content"):
        st.write(content["content"])
        
    # Add expander for additional details if present
    if content.get("details"):
        with st.expander("Meer details"):
            st.write(content["details"])