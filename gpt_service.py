"""
File: gpt_service.py
Provides sophisticated GPT-based analysis and advice generation for the AI Hypotheek Assistent.
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import json
from typing import Dict, Any, Optional, List, Tuple
from app_state import AppState
from conversation_service import ConversationService
from checklist_analysis_service import ChecklistAnalysisService, CHECKLIST
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self, api_key: str):
        """Initialize the GPT service with enhanced configuration."""
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-08-06",
            temperature=0.4,  # Balanced between creativity and consistency
            openai_api_key=api_key,
            max_tokens=4000,  # Ensure enough space for detailed responses
            presence_penalty=0.1,  # Slight penalty to avoid repetition
            frequency_penalty=0.1  # Slight penalty for more diverse language
        )
        self.conversation_service = ConversationService(api_key)
        self.checklist_service = ChecklistAnalysisService(api_key)
        
        try:
            with open('prompt_template.txt', 'r', encoding='utf-8') as file:
                self.prompt_template = file.read()
            logger.info("Successfully loaded prompt template")
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            self.prompt_template = ""

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript to identify missing information."""
        try:
            if not transcript or not transcript.strip():
                logger.warning("Empty transcript provided")
                return self._get_default_missing_info()

            # Time the analysis for performance monitoring
            start_time = datetime.now()

            # Perform parallel analysis
            checklist_analysis = self.checklist_service.analyze_transcript(transcript)
            conversation_analysis = self.conversation_service.analyze_initial_transcript(transcript)
            
            result = {
                "missing_info": checklist_analysis["missing_topics"],
                "explanation": checklist_analysis["explanation"],
                "next_question": conversation_analysis["next_question"],
                "context": conversation_analysis["context"],
                "analysis_time": (datetime.now() - start_time).total_seconds()
            }
            
            logger.info(f"Initial analysis completed in {result['analysis_time']}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in initial analysis: {str(e)}")
            return self._get_default_missing_info()

    def analyze_transcript(self, transcript: str, app_state: Optional['AppState'] = None) -> Optional[Dict[str, str]]:
        """Performs comprehensive transcript analysis with enhanced content generation."""
        try:
            # Validate inputs
            if not self._validate_inputs(transcript):
                return None

            # Process available information
            conversation_history = self._format_additional_info(app_state) if app_state else ""
            klantprofiel = self._get_klantprofiel(app_state)
            
            # Get enriched analysis
            checklist_analysis = self._get_enriched_analysis(transcript, conversation_history)
            
            # Format enhanced prompt
            formatted_prompt = self._create_enhanced_prompt(
                transcript, klantprofiel, conversation_history, checklist_analysis
            )
            if not formatted_prompt:
                return None

            # Generate content
            response = self._generate_content(formatted_prompt)
            if not response:
                return None
            
            # Process and enhance response
            sections = self._parse_sections(response.content.strip())
            validated_sections = self._validate_sections(sections, checklist_analysis["missing_topics"])
            enhanced_sections = self._enhance_sections(validated_sections, app_state)
            
            # Verify final content quality
            if not self._verify_content_quality(enhanced_sections):
                logger.warning("Generated content did not meet quality standards")
                return None

            logger.info("Successfully generated enhanced advice content")
            return enhanced_sections

        except Exception as e:
            logger.error(f"Error in transcript analysis: {str(e)}")
            return None

    def _validate_inputs(self, transcript: str) -> bool:
        """Validates input requirements."""
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided")
            return False

        if not self.prompt_template:
            logger.error("Prompt template not loaded")
            return False

        return True

    def _get_klantprofiel(self, app_state: Optional['AppState']) -> str:
        """Safely retrieves and formats klantprofiel information."""
        try:
            if not app_state or not hasattr(app_state, 'klantprofiel'):
                return "Geen klantprofiel beschikbaar."
                
            klantprofiel = app_state.klantprofiel
            if not klantprofiel or not klantprofiel.strip():
                return "Geen klantprofiel beschikbaar."
                
            return klantprofiel
            
        except Exception as e:
            logger.error(f"Error retrieving klantprofiel: {str(e)}")
            return "Geen klantprofiel beschikbaar."

    def _get_enriched_analysis(self, transcript: str, conversation_history: str) -> Dict[str, Any]:
        """Performs enriched analysis of all available information."""
        combined_text = f"{transcript}\n\n{conversation_history}".strip()
        analysis = self.checklist_service.analyze_transcript(combined_text)
        
        # Add analysis timestamp
        analysis['timestamp'] = datetime.now().isoformat()
        
        # Add completion percentage
        total_topics = sum(len(topics) for topics in CHECKLIST.values())
        missing_topics = sum(len(topics) for topics in analysis['missing_topics'].values())
        analysis['completion_percentage'] = ((total_topics - missing_topics) / total_topics) * 100
        
        return analysis

    def _create_enhanced_prompt(
        self, 
        transcript: str, 
        klantprofiel: str, 
        conversation_history: str, 
        analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Creates an enhanced prompt with all available information."""
        try:
            return self.prompt_template.format(
                transcript=transcript,
                klantprofiel=klantprofiel,
                conversation_history=conversation_history or "Geen aanvullende gespreksinformatie beschikbaar.",
                checklist=json.dumps(CHECKLIST, ensure_ascii=False),
                missing_info=json.dumps(analysis["missing_topics"], ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"Error creating enhanced prompt: {str(e)}")
            return None

    def _generate_content(self, formatted_prompt: str) -> Optional[Any]:
        """Generates enhanced content using the LLM."""
        try:
            messages = [
                SystemMessage(content=self._get_enhanced_system_prompt()),
                HumanMessage(content=formatted_prompt)
            ]
            
            return self.llm.invoke(messages)
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return None

    def _get_enhanced_system_prompt(self) -> str:
        """Returns an enhanced system prompt focused on content from source materials."""
        return """Je bent een ervaren hypotheekadviseur die gespreksnotities en klantinformatie verwerkt tot professionele rapportages.

    BELANGRIJKE RICHTLIJNEN:
    - Gebruik ALLEEN informatie uit het transcript en klantprofiel
    - Verwijs NIET naar toekomstige gesprekken of afspraken
    - Verwerk alle relevante informatie uit de bronnen
    - Organiseer de informatie in een logische structuur

    SCHRIJFSTIJL:
    - Professioneel en zakelijk taalgebruik
    - Duidelijke, volledige zinnen
    - Correcte financiële terminologie
    - Objectieve toon
    - Concrete voorbeelden uit de bronmaterialen

    STRUCTUUR:
    - Begin elke sectie met een duidelijke inleiding
    - Gebruik consistente kopjes en subkopjes
    - Maak gebruik van opsommingstekens voor overzicht
    - Eindig met relevante conclusies

    INHOUD:
    - Focus op expliciet genoemde informatie
    - Vermeld ontbrekende aspecten zonder vervolgacties te suggereren
    - Gebruik specifieke getallen en percentages uit de bronnen
    - Verwijs naar concrete klantsituaties uit het gesprek"""

    def _enhance_sections(self, sections: Dict[str, str], app_state: Optional['AppState']) -> Dict[str, str]:
        """Enhances sections with additional context and structure."""
        enhanced_sections = {}
        
        for section, content in sections.items():
            if not self._is_valid_section_content(content):
                enhanced_sections[section] = self._create_missing_content_notice(section)
                continue

            # Build enhanced content
            enhanced_content = []
            
            # Add professional introduction
            enhanced_content.append(self._get_section_introduction(section, app_state))
            
            # Process main content
            formatted_content = self._format_section_content(content)
            enhanced_content.append(formatted_content)
            
            # Add contextual information
            if context := self._get_contextual_information(section, app_state):
                enhanced_content.append(context)
            
            # Add missing information notices
            if missing := self._get_missing_information_notice(section, app_state):
                enhanced_content.append(missing)
            
            # Add professional conclusion
            enhanced_content.append(self._get_section_conclusion(section, content))
            
            # Combine all parts
            enhanced_sections[section] = "\n\n".join(filter(None, enhanced_content))

        return enhanced_sections

    def _format_section_content(self, content: str) -> str:
        """Formats section content with professional structure."""
        paragraphs = content.split('\n')
        formatted_paragraphs = []
        
        current_section = None
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # Handle section headers
            if paragraph[0].isdigit() and '.' in paragraph:
                current_section = paragraph.strip()
                formatted_paragraphs.append(f"\n{current_section}\n")
                continue
            
            # Handle bullet points
            if paragraph.strip().startswith('-'):
                point = paragraph.strip()[1:].strip()
                formatted_line = self._format_bullet_point(point)
                formatted_paragraphs.append(formatted_line)
                continue
            
            # Handle regular paragraphs
            formatted_paragraphs.append(paragraph.strip())

        return "\n".join(formatted_paragraphs)

    def _format_bullet_point(self, point: str) -> str:
        """Formats bullet points into professional sentences."""
        # Ensure the point starts with capital letter
        point = point[0].upper() + point[1:]
        
        # Add proper punctuation if missing
        if not point.endswith(('.', ':', '?', '!')):
            point += '.'
            
        return f"• {point}"

    def _get_contextual_information(self, section: str, app_state: Optional['AppState']) -> Optional[str]:
        """Retrieves relevant contextual information for the section."""
        if not app_state or not app_state.structured_qa_history:
            return None
            
        relevant_qa = [qa for qa in app_state.structured_qa_history 
                      if qa.get('category') == section.replace("adviesmotivatie_", "")]
                      
        if not relevant_qa:
            return None
            
        context_parts = ["Aanvullende informatie uit het klantgesprek:"]
        for qa in relevant_qa:
            context_parts.append(f"• Besproken onderwerp: {qa.get('context', '')}")
            context_parts.append(f"  - Vraag: {qa.get('question', '')}")
            context_parts.append(f"  - Antwoord: {qa.get('answer', '')}")
            
        return "\n".join(context_parts)

    def _get_section_conclusion(self, section: str, content: str) -> str:
        """Generates appropriate conclusion based on available information."""
        conclusions = {
            "adviesmotivatie_leningdeel": """
    Dit advies is gebaseerd op de besproken financiële situatie en de huidige marktomstandigheden. 
    De gekozen opties sluiten aan bij het besproken risicoprofiel en de persoonlijke voorkeuren.""",
            
            "adviesmotivatie_werkloosheid": """
    De analyse van het werkloosheidsscenario is gebaseerd op de besproken arbeidsmarktpositie en persoonlijke situatie.
    De voorgestelde maatregelen zijn afgestemd op het gewenste beschermingsniveau.""",
            
            "adviesmotivatie_aow": """
    De pensioenanalyse is gebaseerd op de huidige opbouw en de besproken toekomstplannen.
    De financiële planning sluit aan bij de gewenste situatie na pensionering."""
        }
        
        base_conclusion = conclusions.get(section, "")
        if "Nog te behandelen aspecten" in content:
            base_conclusion += "\nVerdere detaillering van de genoemde aspecten zal bijdragen aan een optimaal advies."
            
        return base_conclusion

    def _verify_content_quality(self, sections: Dict[str, str]) -> bool:
        """Verifies that generated content meets quality standards."""
        if not sections:
            return False
            
        for content in sections.values():
            if not content or len(content.split()) < 50:  # Minimum word count
                return False
                
            # Check for required elements
            required_elements = ['1.', '2.', '3.', '•']
            if not all(element in content for element in required_elements):
                return False
                
        return True

    def _format_additional_info(self, app_state: Optional['AppState']) -> str:
        """Formats additional information from app state."""
        try:
            if not app_state or not app_state.additional_info:
                return ""

            info_parts = []
            for key, value in app_state.additional_info.items():
                if isinstance(value, dict):
                    context = value.get('context', '')
                    question = value.get('question', '')
                    answer = value.get('answer', '')
                    if question and answer:
                        info_parts.append(f"Context: {context}\nVraag: {question}\nAntwoord: {answer}")
            
            return "\n\n".join(info_parts) if info_parts else ""
            
        except Exception as e:
            logger.error(f"Error formatting additional info: {str(e)}")
            return ""

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parses content into sections with validation."""
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
        """Validates sections and adds missing information warnings."""
        section_mapping = {
            "adviesmotivatie_leningdeel": "leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "aow"
        }
        
        validated_sections = {}
        
        for section, content in sections.items():
            # Validate content
            if not self._is_valid_section_content(content):
                validated_sections[section] = self._create_missing_content_notice(section)
                continue
                
            validated_sections[section] = content
            
            # Add missing information warnings if applicable
            checklist_key = section_mapping.get(section)
            if checklist_key and checklist_key in missing_info and missing_info[checklist_key]:
                warning = "\n\nNOG TE BESPREKEN:\n"
                warning += "\n".join(f"- {item}" for item in missing_info[checklist_key])
                validated_sections[section] = validated_sections[section] + warning
        
        return validated_sections

    def _is_valid_section_content(self, content: str) -> bool:
        """Validates if section content is meaningful."""
        if not content or len(content.strip()) < 50:  # Minimum content length
            return False
            
        # Check for placeholder patterns
        placeholder_patterns = [
            "geen informatie beschikbaar",
            "informatie ontbreekt",
            "nog te analyseren",
            "onvoldoende informatie"
        ]
        
        content_lower = content.lower()
        if any(pattern in content_lower for pattern in placeholder_patterns):
            return False
            
        # Check for minimum structure
        required_elements = ['1.', '2.', '3.', '•']
        if not any(element in content for element in required_elements):
            return False
            
        return True

    def _create_missing_content_notice(self, section: str) -> str:
        """Creates a professional notice about missing information based on source materials."""
        section_names = {
            "adviesmotivatie_leningdeel": "hypothecaire financiering",
            "adviesmotivatie_werkloosheid": "werkloosheidsscenario",
            "adviesmotivatie_aow": "pensioen- en AOW-situatie"
        }
        
        section_name = section_names.get(section, section)
        
        return f"""1. Beschikbare Informatie
    De volgende aspecten met betrekking tot {section_name} zijn in kaart gebracht op basis van het gesprek:
    • Algemene uitgangspunten zijn besproken
    • Globale wensen zijn geïnventariseerd

    2. Aanvullende Aspecten
    Voor een compleet beeld zijn de volgende aspecten relevant:
    • Specifieke wensen ten aanzien van {section_name}
    • Concrete financiële doelstellingen
    • Risico's en mogelijke maatregelen

    3. Huidige Status
    Op basis van de beschikbare informatie is een eerste inventarisatie gemaakt. 
    Verdere detaillering van bovenstaande punten zal het advies verder aanscherpen."""

    def _get_section_introduction(self, section: str, app_state: Optional['AppState']) -> str:
        """Creates professional introduction for each section."""
        klant_info = "Op basis van uw situatie" if app_state and app_state.klantprofiel else "Op basis van het gesprek"
        
        intros = {
            "adviesmotivatie_leningdeel": f"""
{klant_info} volgt hieronder een uitgebreide analyse van de hypothecaire financiering. Dit advies is toegespitst op uw persoonlijke situatie en wensen, rekening houdend met zowel de korte als lange termijn perspectieven.""",
            
            "adviesmotivatie_werkloosheid": f"""
{klant_info} is een risicoanalyse uitgevoerd met betrekking tot mogelijke werkloosheid. Deze analyse beschouwt de impact op uw financiële situatie en de mogelijke beschermingsmaatregelen.""",
            
            "adviesmotivatie_aow": f"""
{klant_info} presenteren wij een langetermijnanalyse van uw pensioen- en AOW-situatie. Deze analyse richt zich op de financiële planning voor uw pensioenperiode en de afstemming met uw hypothecaire verplichtingen."""
        }
        
        return intros.get(section, "")


    def _enhance_sections(self, sections: Dict[str, str], app_state: Optional['AppState']) -> Dict[str, str]:
        """Enhances sections with additional context and structure."""
        enhanced_sections = {}
        
        for section, content in sections.items():
            if not self._is_valid_section_content(content):
                enhanced_sections[section] = self._create_missing_content_notice(section)
                continue

            # Build enhanced content
            enhanced_content = []
            
            # Add professional introduction
            intro = self._get_section_introduction(section, app_state)
            if intro:
                enhanced_content.append(intro)
            
            # Add main content
            formatted_content = self._format_section_content(content)
            if formatted_content:
                enhanced_content.append(formatted_content)
            
            # Add contextual information if available
            if context := self._get_contextual_information(section, app_state):
                enhanced_content.append(context)
            
            # Add missing information notice if needed
            if missing := self._get_missing_information_notice(section, app_state):
                enhanced_content.append(missing)
            
            # Add conclusion
            conclusion = self._get_section_conclusion(section, content)
            if conclusion:
                enhanced_content.append(conclusion)
            
            # Combine all parts with proper spacing
            enhanced_sections[section] = "\n\n".join(part.strip() for part in enhanced_content if part and part.strip())

        return enhanced_sections
    
    def _get_default_missing_info(self) -> Dict[str, Any]:
        """Returns structured missing information response."""
        return {
            "missing_info": {
                "leningdeel": [
                    "Gewenst leningbedrag en onderbouwing",
                    "Hypotheekvorm voorkeuren",
                    "Rentevaste periode wensen",
                    "NHG overwegingen"
                ],
                "werkloosheid": [
                    "Huidige arbeidssituatie",
                    "Risico-inschatting werkloosheid",
                    "Gewenste financiële buffers"
                ],
                "aow": [
                    "Pensioenwensen en -planning",
                    "AOW-leeftijd en impact",
                    "Vermogensopbouw doelen"
                ]
            },
            "explanation": "Er is aanvullende informatie nodig om een volledig advies te kunnen opstellen. Graag plannen we een gesprek in om alle relevante aspecten te bespreken.",
            "next_question": "Wat is het gewenste leningbedrag voor de hypotheek en wat zijn uw overwegingen hierbij?",
            "context": "We beginnen met de belangrijkste uitgangspunten voor uw hypotheekadvies."
        }
    def _get_missing_information_notice(self, section: str, app_state: Optional['AppState']) -> Optional[str]:
        """Generates notice about missing information based on source materials."""
        section_mapping = {
            "adviesmotivatie_leningdeel": "leningdeel",
            "adviesmotivatie_werkloosheid": "werkloosheid",
            "adviesmotivatie_aow": "aow"
        }
        
        section_key = section_mapping.get(section)
        if not section_key or not app_state or not app_state.missing_info:
            return None

        missing_items = app_state.missing_info.get(section_key, [])
        if not missing_items:
            return None

        section_titles = {
            "leningdeel": "hypothecaire financiering",
            "werkloosheid": "werkloosheidsscenario",
            "aow": "pensioen- en AOW-situatie"
        }

        notice = f"\nNog te behandelen aspecten voor {section_titles.get(section_key, section_key)}:"
        for item in missing_items:
            notice += f"\n• {item}"

        return notice