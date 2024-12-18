"""
File: fp_analysis_service.py
Handles the analysis of transcripts and klantprofiel for FP module.
"""

import streamlit as st
from typing import Dict, Any, List
import json
from langchain_openai import ChatOpenAI

class FPAnalysisService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            openai_api_key=api_key
        )

    def analyze_section(self, transcript: str, klantprofiel: str, section: str) -> Dict[str, Any]:
        """Analyzes input for a specific FP section."""
        system_prompt = self._get_section_prompt(section)
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
                Analyze this input for the {section} section:
                
                TRANSCRIPT:
                {transcript}
                
                KLANTPROFIEL:
                {klantprofiel}
                """}
            ]
            
            response = self.llm.invoke(messages)
            return json.loads(response.content)
            
        except Exception as e:
            st.error(f"Error analyzing section {section}: {str(e)}")
            return self._get_default_analysis(section)

    def _get_section_prompt(self, section: str) -> str:
        """Gets the appropriate prompt for each section."""
        prompts = {
            "samenvatting": """Analyze the input and extract:
                - Netto besteedbaar inkomen
                - Key financial goals
                - Core advice points
                
                Return in JSON format:
                {
                    "netto_besteedbaar_inkomen": "amount + explanation",
                    "hoofdpunten": ["point1", "point2", ...],
                    "kernadvies": "summary of main advice"
                }""",
            
            "situatie_later": """Analyze retirement situation and return:
                {
                    "voor_advies": {
                        "content": "current situation",
                        "years": [2024, 2025...],
                        "values": [value1, value2...]
                    },
                    "na_advies": {
                        "content": "situation after advice",
                        "years": [2024, 2025...],
                        "values": [value1, value2...]
                    }
                }""",
                
            # Add prompts for other sections...
        }
        
        return prompts.get(section, "Analyze the input and extract relevant information.")

    def _get_default_analysis(self, section: str) -> Dict[str, Any]:
        """Returns default analysis structure for a section."""
        defaults = {
            "samenvatting": {
                "netto_besteedbaar_inkomen": "Nog te bepalen",
                "hoofdpunten": ["Informatie niet beschikbaar"],
                "kernadvies": "Nadere analyse nodig"
            },
            "situatie_later": {
                "voor_advies": {"content": "Nog te analyseren"},
                "na_advies": {"content": "Nog te bepalen"}
            }
        }
        return defaults.get(section, {"content": "Nog te analyseren"})