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
from conversation_service import ConversationService
from checklist_analysis_service import ChecklistAnalysisService, CHECKLIST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-08-06",
            temperature=0.2,  # Reduced temperature for more consistent output
            openai_api_key=api_key
        )
        self.conversation_service = ConversationService(api_key)
        self.checklist_service = ChecklistAnalysisService(api_key)
        
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

            # Use checklist service for initial analysis
            checklist_analysis = self.checklist_service.analyze_transcript(transcript)
            
            # Use conversation service to generate appropriate questions
            conversation_analysis = self.conversation_service.analyze_initial_transcript(transcript)
            
            # Combine analyses
            result = {
                "missing_info": checklist_analysis["missing_topics"],
                "explanation": checklist_analysis["explanation"],
                "next_question": conversation_analysis["next_question"],
                "context": conversation_analysis["context"]
            }
            
            logger.info(f"Combined analysis result: {result}")
            return result
            
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

            # Get conversation history and additional info
            conversation_history = self._format_additional_info(app_state)
            
            # Get checklist analysis for remaining gaps
            checklist_analysis = self.checklist_service.analyze_transcript(
                transcript + "\n\n" + conversation_history
            )

            # Format the prompt template with all available information
            formatted_prompt = self.prompt_template.format(
                transcript=transcript,
                conversation_history=conversation_history,
                checklist=json.dumps(CHECKLIST, ensure_ascii=False),
                missing_info=json.dumps(checklist_analysis["missing_topics"], ensure_ascii=False)
            )

            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""Je bent een ervaren hypotheekadviseur die gespecialiseerd is in het analyseren 
                van klantgesprekken en het opstellen van uitgebreide adviesrapporten.
                
                Gebruik de checklist om te controleren of alle belangrijke onderwerpen zijn behandeld.
                Identificeer eventuele ontbrekende informatie en geef duidelijk aan wat er nog besproken moet worden.
                
                Baseer je advies ALLEEN op expliciet genoemde informatie uit het transcript en de aanvullende gesprekken."""),
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

            sections = self._parse_sections(content)
            
            # Add missing information warnings to each section
            sections = self._add_missing_info_warnings(sections, checklist_analysis["missing_topics"])
            
            return sections
            
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

    def _add_missing_info_warnings(self, sections: Dict[str, str], missing_info: Dict[str, list]) -> Dict[str, str]:
        """Adds warnings about missing information to each section."""
        section_mapping = {
            "adviesmotivatie_leningdeel": "leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "aow"
        }
        
        for section, content in sections.items():
            checklist_key = section_mapping.get(section)
            if checklist_key and checklist_key in missing_info and missing_info[checklist_key]:
                warning = "\n\nLET OP - Ontbrekende informatie:\n"
                warning += "\n".join(f"- {item}" for item in missing_info[checklist_key])
                sections[section] = content + warning
        
        return sections

    def _get_default_missing_info(self) -> Dict[str, Any]:
        """Returns default missing information structure."""
        return {
            "missing_info": CHECKLIST,
            "explanation": "Transcript bevat onvoldoende informatie voor analyse",
            "next_question": "Kun je me vertellen wat het gewenste leningbedrag is?",
            "context": "We beginnen met de basisinformatie voor je hypotheekaanvraag."
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
