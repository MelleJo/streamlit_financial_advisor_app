"""
File: gpt_service.py
Provides GPT-based analysis and advice generation for the AI Hypotheek Assistent.
This service handles all interactions with OpenAI's GPT models, providing two main functions:
1. Initial transcript analysis to identify missing information in mortgage advice conversations
2. Comprehensive analysis of transcripts to generate structured mortgage advice reports
The service includes robust error handling, default responses, and structured output formatting
using XML tags for consistent advice sections (loan details, unemployment risks, and retirement planning).
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import json
from typing import Dict, Any, Optional
from app_state import AppState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-08-06",
            temperature=0.2,  # Reduced temperature for more consistent output
            openai_api_key=api_key
        )
        # Load the prompt template during initialization
        try:
            with open('prompt_template.txt', 'r', encoding='utf-8') as file:
                self.prompt_template = file.read()
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            self.prompt_template = ""

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript to identify missing information."""
        try:
            if not transcript or len(transcript.strip()) == 0:
                logger.warning("Empty transcript provided")
                return self._get_default_missing_info()

            # More specific system prompt
            system_prompt = """Je bent een ervaren hypotheekadviseur.
            Je MOET antwoorden in exact het gevraagde JSON format.
            GEEN markdown codeblocks (geen ```json). ALLEEN pure JSON."""
            
            # More specific user prompt with example
            user_prompt = f"""
            Analyseer dit transcript:
            {transcript}
            
            Je MOET je antwoord geven in exact dit JSON formaat:
            {{
                "missing_info": {{
                    "leningdeel": [
                        "leningbedrag",
                        "NHG keuze",
                        "rentevaste periode",
                        "hypotheekvorm"
                    ],
                    "werkloosheid": [
                        "huidige arbeidssituatie",
                        "werkloosheidsrisico",
                        "gewenste dekking"
                    ],
                    "aow": [
                        "pensioenleeftijd",
                        "pensioenwensen",
                        "vermogensopbouw"
                    ]
                }}
            }}
            ALLEEN DIT FORMAT. Geen extra tekst ervoor of erna. Geen markdown code blocks."""

            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            messages = prompt.format_messages()
            response = self.llm.invoke(messages)
            
            content = response.content.strip()
            logger.info(f"Initial analysis response: {content}")
            
            # Clean up the response by removing markdown code blocks if present
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Try to parse JSON, if fails return default
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {content}")
                return self._get_default_missing_info()
            
        except Exception as e:
            logger.error(f"Error in initial analysis: {str(e)}")
            return self._get_default_missing_info()

    def analyze_transcript(self, transcript: str, app_state: Optional['AppState'] = None) -> Dict[str, str]:
        """Analyzes the transcript and additional information to generate advice."""
        try:
            if not transcript:
                return self._get_default_sections()

            if not self.prompt_template:
                logger.error("Prompt template not loaded")
                return self._get_default_sections()

            # Prepare additional info
            conversation_history = self._format_additional_info(app_state)

            # Format the prompt template with the transcript and conversation history
            formatted_prompt = self.prompt_template.format(
                transcript=transcript,
                conversation_history=conversation_history
            )

            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="Je bent een ervaren hypotheekadviseur die gespecialiseerd is in het analyseren van klantgesprekken en het opstellen van uitgebreide adviesrapporten."),
                HumanMessage(content=formatted_prompt)
            ])

            messages = prompt.format_messages()
            response = self.llm.invoke(messages)
            
            content = response.content.strip()
            logger.info(f"Analysis response: {content}")
            
            # Check if response contains required tags
            if not all(tag in content for tag in ['<adviesmotivatie_leningdeel>', '<adviesmotivatie_werkloosheid>', '<adviesmotivatie_aow>']):
                logger.error("Response missing required tags")
                return self._get_default_sections()

            return self._parse_sections(content)
            
        except Exception as e:
            logger.error(f"Error in transcript analysis: {str(e)}")
            return self._get_default_sections()

    def _format_additional_info(self, app_state: Optional['AppState']) -> str:
        """Safely formats additional information from app state."""
        try:
            if not app_state or not hasattr(app_state, 'additional_info') or not app_state.additional_info:
                return "Geen aanvullende informatie beschikbaar."

            info_parts = []
            for key, value in app_state.additional_info.items():
                if isinstance(value, dict):
                    question = value.get('question', '')
                    answer = value.get('answer', '')
                    if question and answer:
                        info_parts.append(f"Vraag: {question}\nAntwoord: {answer}")
            
            return "\n\n".join(info_parts) if info_parts else "Geen aanvullende informatie beschikbaar."
            
        except Exception as e:
            logger.error(f"Error formatting additional info: {str(e)}")
            return "Error bij verwerken aanvullende informatie."

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parses content into sections with error handling."""
        sections = {
            "adviesmotivatie_leningdeel": "",
            "adviesmotivatie_werkloosheid": "",
            "adviesmotivatie_aow": ""
        }
        
        try:
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('<adviesmotivatie_'):
                    current_section = line[1:-1]
                    current_content = []
                elif line.startswith('</adviesmotivatie_'):
                    if current_section in sections:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = None
                elif current_section:
                    current_content.append(line)

            # Validate sections
            for section, content in sections.items():
                if not content.strip():
                    sections[section] = self._get_default_section_content(section)
                    
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing sections: {str(e)}")
            return self._get_default_sections()

    def _get_default_missing_info(self) -> Dict[str, Any]:
        """Returns default missing information structure."""
        return {
            "missing_info": {
                "leningdeel": ["leningbedrag", "NHG keuze", "rentevaste periode", "hypotheekvorm"],
                "werkloosheid": ["huidige arbeidssituatie", "werkloosheidsrisico", "gewenste dekking"],
                "aow": ["pensioenleeftijd", "pensioenwensen", "vermogensopbouw"]
            }
        }

    def _get_default_sections(self) -> Dict[str, str]:
        """Returns default sections with explanatory content."""
        return {
            "adviesmotivatie_leningdeel": self._get_default_section_content("adviesmotivatie_leningdeel"),
            "adviesmotivatie_werkloosheid": self._get_default_section_content("adviesmotivatie_werkloosheid"),
            "adviesmotivatie_aow": self._get_default_section_content("adviesmotivatie_aow")
        }

    def _get_default_section_content(self, section: str) -> str:
        """Returns default content for a specific section."""
        defaults = {
            "adviesmotivatie_leningdeel": """
1. Samenvatting leningdeel
- Onvoldoende informatie voor volledig advies
- Basisgegevens ontbreken

2. Ontbrekende informatie
- Gewenst leningbedrag
- NHG voorkeuren
- Rentevaste periode wensen
- Gewenste hypotheekvorm

3. Aanbevelingen
- Plan een vervolggesprek
- Verzamel basisgegevens
- Bepaal klantvoorkeuren
""",
            "adviesmotivatie_werkloosheid": """
1. Samenvatting werkloosheidsrisico
- Onvoldoende informatie voor risico-inschatting
- Werkloosheidsdekking niet bepaald

2. Ontbrekende informatie
- Huidige arbeidssituatie
- Werkloosheidsrisico inschatting
- Gewenste dekking

3. Aanbevelingen
- Analyseer arbeidssituatie
- Bespreek risicotolerantie
- Onderzoek verzekeringsopties
""",
            "adviesmotivatie_aow": """
1. Samenvatting pensioensituatie
- Onvoldoende informatie voor pensioenadvies
- Toekomstplanning onduidelijk

2. Ontbrekende informatie
- AOW-leeftijd
- Pensioenwensen
- Vermogensopbouw plan

3. Aanbevelingen
- Breng pensioenopbouw in kaart
- Bepaal gewenste pensioensituatie
- Plan vermogensopbouw strategie
"""
        }
        return defaults.get(section, "Geen informatie beschikbaar voor deze sectie.")
