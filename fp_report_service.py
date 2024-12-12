"""
File: fp_report_service.py
Handles PDF and DOCX report generation for the FP module.
"""

import streamlit as st
import plotly.graph_objects as go
from docx import Document
from docx.shared import Inches, Pt
from datetime import datetime
import io

class FPReportService:
    @staticmethod
    def create_situation_graph(voor_data: dict, na_data: dict) -> go.Figure:
        """Creates a comparison graph for situations."""
        fig = go.Figure()

        # Add traces for before and after
        fig.add_trace(go.Scatter(
            x=voor_data.get("years", []),
            y=voor_data.get("values", []),
            name="Voor advies",
            line=dict(color='#1f77b4')
        ))

        fig.add_trace(go.Scatter(
            x=na_data.get("years", []),
            y=na_data.get("values", []),
            name="Na advies",
            line=dict(color='#2ca02c')
        ))

        # Update layout
        fig.update_layout(
            title="Situatie Vergelijking",
            xaxis_title="Jaren",
            yaxis_title="Waarde (€)",
            showlegend=True
        )

        return fig

    @staticmethod
    def generate_docx(fp_state) -> io.BytesIO:
        """Generates a DOCX report based on the FP state."""
        doc = Document()
        
        # Add title
        doc.add_heading('Financieel Plan Rapport', 0)
        doc.add_paragraph(f'Gegenereerd op: {datetime.now().strftime("%d-%m-%Y")}')
        
        # Add sections
        sections = [
            ("Samenvatting", fp_state.samenvatting),
            ("Uitwerking Advies", fp_state.uitwerking_advies),
            ("Huidige Situatie", fp_state.huidige_situatie),
            ("Situatie Later", fp_state.situatie_later),
            ("Situatie Overlijden", fp_state.situatie_overlijden),
            ("Situatie Arbeidsongeschiktheid", fp_state.situatie_arbeidsongeschiktheid),
            ("Erven en Schenken", fp_state.erven_schenken),
            ("Actiepunten", fp_state.actiepunten)
        ]

        for title, content in sections:
            doc.add_heading(title, level=1)
            if isinstance(content, dict):
                for key, value in content.items():
                    if key != "graphs":  # Skip graph data in DOCX
                        if isinstance(value, list):
                            for item in value:
                                doc.add_paragraph(f"• {item}", style='List Bullet')
                        else:
                            doc.add_paragraph(str(value))
            doc.add_paragraph()  # Add spacing

        # Save to memory
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        return docx_buffer

    @staticmethod
    def format_section_content(content: dict) -> str:
        """Formats section content for display."""
        if not content:
            return ""
        
        formatted = []
        for key, value in content.items():
            if key != "graphs":
                if isinstance(value, list):
                    formatted.extend([f"• {item}" for item in value])
                else:
                    formatted.append(str(value))
        
        return "\n".join(formatted)