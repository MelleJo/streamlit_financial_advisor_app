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

    def _is_valid_section_content(self, content: str) -> bool:
        """Validates if section content is meaningful and not just placeholder text."""
        if not content or len(content.strip()) < 10:
            return False
            
        # Check for actual content vs. placeholder patterns
        placeholder_patterns = [
            "Geen informatie beschikbaar",
            "Informatie ontbreekt",
            "Nog te analyseren",
            "Onvoldoende informatie"
        ]
        
        content_lower = content.lower()
        if any(pattern.lower() in content_lower for pattern in placeholder_patterns):
            return False
            
        # Check for minimum structure (should have at least one heading and some content)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if len(lines) < 3:  # Need at least a heading and some content
            return False
            
        return True
    
    def analyze_transcript(self, transcript: str, app_state: Optional['AppState'] = None) -> Optional[Dict[str, str]]:
        """Analyzes the transcript and additional information to generate advice."""
        try:
            # Validate transcript
            if not transcript or not transcript.strip():
                logger.warning("Empty transcript provided")
                return None

            if not self.prompt_template:
                logger.error("Prompt template not loaded")
                return None

            # Get conversation history and additional info
            conversation_history = self._format_additional_info(app_state) if app_state else ""
            
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

            messages = [
                SystemMessage(content="""Je bent een ervaren hypotheekadviseur die gespecialiseerd is in het analyseren 
                van klantgesprekken en het opstellen van uitgebreide adviesrapporten.
                
                Gebruik de checklist om te controleren of alle belangrijke onderwerpen zijn behandeld.
                Als er geen informatie beschikbaar is, geef dit dan duidelijk aan.
                
                BELANGRIJK: Geef ALLEEN informatie die expliciet genoemd is in het transcript."""),
                HumanMessage(content=formatted_prompt)
            ]

            response = self.llm.invoke(messages)
            
            if not response or not response.content.strip():
                logger.error("Empty response from LLM")
                return None
                
            content = response.content.strip()
            
            # Parse sections and validate content
            sections = self._parse_sections(content)
            
            # Only return if we have valid content
            if any(content.strip() for content in sections.values()):
                return sections
            else:
                logger.warning("No valid content in parsed sections")
                return None
                
        except Exception as e:
            logger.error(f"Error in transcript analysis: {str(e)}")
            return None

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
        """Parses content into sections with improved validation."""
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
                        section_content = '\n'.join(current_content)
                        if self._is_valid_section_content(section_content):
                            sections[current_section] = section_content
                        else:
                            sections[current_section] = self._create_missing_content_notice(current_section)
                    current_section = None
                elif current_section:
                    current_content.append(line)

            return sections
                
        except Exception as e:
            logger.error(f"Error parsing sections: {str(e)}")
            return self._get_default_sections()


    def _create_missing_content_notice(self, section: str) -> str:
        """Creates a clear notice about missing information without placeholder content."""
        section_names = {
            "adviesmotivatie_leningdeel": "het leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "AOW en pensioen"
        }
        
        section_name = section_names.get(section, section)
        
        return f"""1. Ontbrekende Informatie
        
    Er is in het gesprek geen concrete informatie besproken over {section_name}. 
    Een vervolgsgesprek is nodig om de volgende aspecten te bespreken:

    2. Benodigde Informatie
    - Specifieke wensen en voorkeuren
    - Concrete situatie en plannen
    - Risico's en mogelijke oplossingen

    3. Advies
    Een volledig advies kan worden opgesteld nadat bovenstaande informatie is besproken tijdens een vervolgafspraak."""


    def _validate_sections(self, sections: Dict[str, str], missing_info: Dict[str, list]) -> Dict[str, str]:
        """Validates and enhances sections with missing information warnings."""
        section_mapping = {
            "adviesmotivatie_leningdeel": "leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "aow"
        }
        
        validated_sections = {}
        
        for section, content in sections.items():
            checklist_key = section_mapping.get(section)
            
            if not self._is_valid_section_content(content):
                validated_sections[section] = self._create_missing_content_notice(section)
            else:
                validated_sections[section] = content
                
            # Add missing information warnings if applicable
            if checklist_key and checklist_key in missing_info and missing_info[checklist_key]:
                warning = "\n\nNOG TE BESPREKEN:\n"
                warning += "\n".join(f"- {item}" for item in missing_info[checklist_key])
                validated_sections[section] = validated_sections[section] + warning
        
        return validated_sections

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
