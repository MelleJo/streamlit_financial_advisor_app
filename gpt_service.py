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
            temperature=0.2,
            openai_api_key=api_key
        )
        self.conversation_service = ConversationService(api_key)
        self.checklist_service = ChecklistAnalysisService(api_key)
        
        try:
            with open('prompt_template.txt', 'r', encoding='utf-8') as file:
                self.prompt_template = file.read()
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            self.prompt_template = ""

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        try:
            if not transcript or not transcript.strip():
                logger.warning("Empty transcript provided")
                return self._get_default_missing_info()

            checklist_analysis = self.checklist_service.analyze_transcript(transcript)
            conversation_analysis = self.conversation_service.analyze_initial_transcript(transcript)
            
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

    def analyze_transcript(self, transcript: str, app_state: Optional['AppState'] = None) -> Optional[Dict[str, str]]:
        try:
            if not transcript or not transcript.strip():
                logger.warning("Empty transcript provided")
                return None

            if not self.prompt_template:
                logger.error("Prompt template not loaded")
                return None

            conversation_history = self._format_additional_info(app_state) if app_state else ""
            
            checklist_analysis = self.checklist_service.analyze_transcript(
                transcript + "\n\n" + conversation_history
            )

            formatted_prompt = self.prompt_template.format(
                transcript=transcript,
                conversation_history=conversation_history,
                checklist=json.dumps(CHECKLIST, ensure_ascii=False),
                missing_info=json.dumps(checklist_analysis["missing_topics"], ensure_ascii=False)
            )

            messages = [
                SystemMessage(content="""Je bent een ervaren hypotheekadviseur die gespecialiseerd is in het analyseren 
                van klantgesprekken en het opstellen van uitgebreide adviesrapporten.
                
                BELANGRIJK: 
                - Geef ALLEEN informatie die expliciet genoemd is in het transcript
                - Gebruik GEEN placeholder tekst of algemene aannames
                - Als informatie ontbreekt, geef dit expliciet aan"""),
                HumanMessage(content=formatted_prompt)
            ]

            response = self.llm.invoke(messages)
            
            if not response or not response.content.strip():
                logger.error("Empty response from LLM")
                return None
                
            sections = self._parse_sections(response.content.strip())
            validated_sections = self._validate_sections(sections, checklist_analysis["missing_topics"])
            
            return validated_sections if any(content.strip() for content in validated_sections.values()) else None
                
        except Exception as e:
            logger.error(f"Error in transcript analysis: {str(e)}")
            return None

    def _format_additional_info(self, app_state: Optional['AppState']) -> str:
        try:
            if not app_state or not app_state.additional_info:
                return ""

            info_parts = []
            for key, value in app_state.additional_info.items():
                if isinstance(value, dict):
                    question = value.get('question', '')
                    answer = value.get('answer', '')
                    if question and answer:
                        info_parts.append(f"Vraag: {question}\nAntwoord: {answer}")
            
            return "\n\n".join(info_parts) if info_parts else ""
            
        except Exception as e:
            logger.error(f"Error formatting additional info: {str(e)}")
            return ""

    def _parse_sections(self, content: str) -> Dict[str, str]:
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

            return sections
                
        except Exception as e:
            logger.error(f"Error parsing sections: {str(e)}")
            return sections

    def _validate_sections(self, sections: Dict[str, str], missing_info: Dict[str, list]) -> Dict[str, str]:
        section_mapping = {
            "adviesmotivatie_leningdeel": "leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "aow"
        }
        
        validated_sections = {}
        
        for section, content in sections.items():
            if not self._is_valid_section_content(content):
                validated_sections[section] = self._create_missing_content_notice(section)
                continue
                
            validated_sections[section] = content
            
            checklist_key = section_mapping.get(section)
            if checklist_key and checklist_key in missing_info and missing_info[checklist_key]:
                warning = "\n\nNOG TE BESPREKEN:\n"
                warning += "\n".join(f"- {item}" for item in missing_info[checklist_key])
                validated_sections[section] = validated_sections[section] + warning
        
        return validated_sections

    def _is_valid_section_content(self, content: str) -> bool:
        if not content or len(content.strip()) < 10:
            return False
            
        placeholder_patterns = [
            "geen informatie beschikbaar",
            "informatie ontbreekt",
            "nog te analyseren",
            "onvoldoende informatie"
        ]
        
        content_lower = content.lower()
        if any(pattern in content_lower for pattern in placeholder_patterns):
            return False
            
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return len(lines) >= 3

    def _create_missing_content_notice(self, section: str) -> str:
        section_names = {
            "adviesmotivatie_leningdeel": "het leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "AOW en pensioen"
        }
        
        return f"""Er is in het gesprek geen concrete informatie besproken over {section_names.get(section, section)}. 
        
Deze onderwerpen moeten nog besproken worden tijdens een vervolgafspraak:

- Specifieke wensen en voorkeuren
- Concrete situatie
- Risico's en mogelijke oplossingen"""

    def _get_default_missing_info(self) -> Dict[str, Any]:
        return {
            "missing_info": {
                "leningdeel": ["Exacte leningbedrag", "NHG keuze", "Rentevaste periode", "Hypotheekvorm"],
                "werkloosheid": ["Huidige arbeidssituatie", "Werkloosheidsrisico", "Gewenste dekking"],
                "aow": ["AOW-leeftijd", "Pensioenwensen", "Vermogensopbouw"]
            },
            "explanation": "Er is nog onvoldoende informatie beschikbaar voor een volledig advies",
            "next_question": "Wat is het gewenste leningbedrag voor de hypotheek?",
            "context": "We beginnen met de belangrijkste basisgegevens"
        }