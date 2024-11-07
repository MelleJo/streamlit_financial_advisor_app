import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
import json
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-08-06",
            temperature=0.3,
            openai_api_key=api_key
        )
        
        # Conversation history prompt
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die adviesnotities analyseert. 
            Analyseer de notitie met betrekking tot de leningdeel, werkloosheid, en AOW aspecten."""),
            HumanMessage(content="""
            Transcript van de adviesnotitie:
            {transcript}

            Eventuele aanvullende informatie:
            {additional_info}

            Genereer een gestructureerd adviesrapport met de volgende secties:
            
            <adviesmotivatie_leningdeel>
            - Gedetailleerde analyse van het leningdeel
            - Inclusief bedragen, voorwaarden en motivatie
            </adviesmotivatie_leningdeel>

            <adviesmotivatie_werkloosheid>
            - Analyse van werkloosheidsrisico's en maatregelen
            - Inclusief verzekeringen en buffer
            </adviesmotivatie_werkloosheid>

            <adviesmotivatie_aow>
            - Analyse van de pensioensituatie
            - Inclusief AOW en aanvullende voorzieningen
            </adviesmotivatie_aow>
            """)
        ])

    def analyze_transcript(
        self,
        transcript: str,
        app_state: Optional['AppState'] = None
    ) -> Dict[str, str]:
        """Analyzes the transcript and additional information to generate advice."""
        try:
            # Format additional info if available
            additional_info = ""
            if app_state and app_state.additional_info:
                additional_info = "Aanvullende informatie:\n"
                for qa in app_state.additional_info.values():
                    additional_info += f"\nVraag: {qa['question']}\nAntwoord: {qa['answer']}\n"

            # Get response from LLM
            messages = self.analysis_prompt.format_messages(
                transcript=transcript,
                additional_info=additional_info
            )
            response = self.llm.invoke(messages)
            
            # Extract content
            content = response.content
            logger.info(f"Raw LLM response: {content}")
            
            # Parse sections
            sections = {
                "adviesmotivatie_leningdeel": "",
                "adviesmotivatie_werkloosheid": "",
                "adviesmotivatie_aow": ""
            }
            
            current_section = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('<adviesmotivatie_'):
                    current_section = line[1:-1]
                elif line.startswith('</adviesmotivatie_'):
                    current_section = None
                elif current_section and current_section in sections:
                    sections[current_section] += line + '\n'
            
            # Clean up sections
            return {k: v.strip() for k, v in sections.items() if v.strip()}
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return {
                "adviesmotivatie_leningdeel": "Er is een fout opgetreden bij de analyse.",
                "adviesmotivatie_werkloosheid": "Er is een fout opgetreden bij de analyse.",
                "adviesmotivatie_aow": "Er is een fout opgetreden bij de analyse."
            }