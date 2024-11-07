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
        
        # Initial analysis prompt - Modified to force structured output
        self.initial_analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die een initiële analyse uitvoert.
            Je MOET antwoorden in het gevraagde JSON format, geen extra tekst."""),
            HumanMessage(content="""
            Analyseer dit transcript en retourneer ALLEEN een JSON object in exact dit format:
            
            {
                "missing_info": {
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
                }
            }

            Transcript: {transcript}
            """)
        ])
        
        # Full analysis prompt - Modified for more structured output
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die adviesnotities analyseert. 
            Focus op concrete details en cijfers in je analyse."""),
            HumanMessage(content="""
            Transcript van de adviesnotitie:
            {transcript}

            Eventuele aanvullende informatie:
            {additional_info}

            Genereer een gestructureerd adviesrapport met deze exacte secties:
            
            <adviesmotivatie_leningdeel>
            - Leningbedrag en onderbouwing
            - NHG keuze en motivatie
            - Gekozen hypotheekvorm en toelichting
            - Rentevaste periode en overwegingen
            - Maandlasten berekening
            </adviesmotivatie_leningdeel>

            <adviesmotivatie_werkloosheid>
            - Huidige arbeidssituatie
            - Werkloosheidsrisico analyse
            - Benodigde maandelijkse buffer
            - Verzekeringsdekking advies
            </adviesmotivatie_werkloosheid>

            <adviesmotivatie_aow>
            - Verwachte pensioendatum
            - Pensioenopbouw status
            - Hypotheeksituatie bij pensioen
            - Vermogensplanning advies
            </adviesmotivatie_aow>
            """)
        ])

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript to identify missing information."""
        try:
            if not transcript or len(transcript.strip()) == 0:
                return self._get_default_missing_info("Geen transcript aangeleverd")

            messages = self.initial_analysis_prompt.format_messages(transcript=transcript)
            response = self.llm.invoke(messages)
            
            content = response.content.strip()
            logger.info(f"Initial analysis response: {content}")
            
            # If no proper JSON response, return default structure
            if not content or not content.startswith("{"):
                return self._get_default_missing_info("Kon analyse niet uitvoeren")

            try:
                # Remove any markdown formatting if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                result = json.loads(content)
                if not isinstance(result, dict) or "missing_info" not in result:
                    return self._get_default_missing_info("Incorrect response format")
                
                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                return self._get_default_missing_info("Kon JSON niet verwerken")
            
        except Exception as e:
            logger.error(f"Error in initial transcript analysis: {str(e)}")
            return self._get_default_missing_info(f"Analyse error: {str(e)}")

    def _get_default_missing_info(self, error_msg: str) -> Dict[str, Any]:
        """Returns a default structure for missing information."""
        return {
            "missing_info": {
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
            }
        }

    def analyze_transcript(
        self,
        transcript: str,
        app_state: Optional['AppState'] = None
    ) -> Dict[str, str]:
        """Analyzes the transcript and additional information to generate advice."""
        try:
            if not transcript or len(transcript.strip()) == 0:
                return self._get_default_analysis_response("Geen transcript aangeleverd")

            # Format additional info if available
            additional_info = "Geen aanvullende informatie beschikbaar."  # Default value
            if app_state and app_state.additional_info:
                additional_info = "Aanvullende informatie:\n"
                for qa in app_state.additional_info.values():
                    additional_info += f"\nVraag: {qa['question']}\nAntwoord: {qa['answer']}\n"

            # Modified prompt to force structured output even with minimal information
            messages = [
                SystemMessage(content="""Je bent een hypotheekadviseur die adviesnotities analyseert.
                Je MOET ALTIJD antwoorden met de drie gevraagde secties, zelfs als er weinig informatie is.
                Als informatie ontbreekt, geef dan aan wat er mist en wat er nodig is."""),
                HumanMessage(content=f"""
                Transcript van de adviesnotitie:
                {transcript}

                {additional_info}

                Retourneer ALTIJD een analyse in dit format, zelfs bij beperkte informatie:

                <adviesmotivatie_leningdeel>
                - Analyse van beschikbare leningdeel informatie
                - Identificatie van ontbrekende informatie
                - Aanbevelingen voor vervolgstappen
                </adviesmotivatie_leningdeel>

                <adviesmotivatie_werkloosheid>
                - Analyse van beschikbare werkloosheid informatie
                - Identificatie van ontbrekende informatie
                - Aanbevelingen voor vervolgstappen
                </adviesmotivatie_werkloosheid>

                <adviesmotivatie_aow>
                - Analyse van beschikbare AOW informatie
                - Identificatie van ontbrekende informatie
                - Aanbevelingen voor vervolgstappen
                </adviesmotivatie_aow>
                """)
            ]

            # Get response from LLM
            response = self.llm.invoke(messages)
            content = response.content
            logger.info(f"Raw LLM response: {content}")

            # Handle unstructured responses
            if not any(tag in content for tag in ['<adviesmotivatie_leningdeel>', '<adviesmotivatie_werkloosheid>', '<adviesmotivatie_aow>']):
                return {
                    "adviesmotivatie_leningdeel": "Op basis van de beperkte informatie kunnen we nog geen volledig advies geven. We hebben meer details nodig over het gewenste leningbedrag, NHG-wensen, en hypotheekvorm.",
                    "adviesmotivatie_werkloosheid": "Er is meer informatie nodig over de huidige arbeidssituatie en gewenste dekking bij werkloosheid om een gedegen advies te kunnen geven.",
                    "adviesmotivatie_aow": "Voor een AOW-advies hebben we meer details nodig over de pensioenwensen en huidige pensioenopbouw."
                }

            # Parse sections
            sections = {
                "adviesmotivatie_leningdeel": [],
                "adviesmotivatie_werkloosheid": [],
                "adviesmotivatie_aow": []
            }
            
            current_section = None
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('<adviesmotivatie_'):
                    current_section = line.strip('<>')
                elif line.startswith('</adviesmotivatie_'):
                    current_section = None
                elif current_section and current_section in sections:
                    sections[current_section].append(line)

            # Convert to final format with default messages for empty sections
            result = {}
            for section, lines in sections.items():
                if lines:
                    result[section] = '\n'.join(lines)
                else:
                    result[section] = self._get_default_section_content(section)

            return result

        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return self._get_default_analysis_response(f"Error: {str(e)}")

    def _get_default_section_content(self, section: str) -> str:
        """Returns default content for empty sections."""
        defaults = {
            "adviesmotivatie_leningdeel": """
            Er is onvoldoende informatie beschikbaar voor een volledig leningdeel advies.
            
            Benodigde informatie:
            - Gewenst leningbedrag
            - Voorkeur voor NHG
            - Gewenste hypotheekvorm
            - Voorkeuren rentevaste periode
            
            Advies: Plan een vervolggesprek om deze aspecten te bespreken.""",
            
            "adviesmotivatie_werkloosheid": """
            Er is onvoldoende informatie beschikbaar voor een werkloosheidsadvies.
            
            Benodigde informatie:
            - Huidige arbeidssituatie
            - Risicoprofiel
            - Gewenste dekking
            - Buffer mogelijkheden
            
            Advies: Bespreek deze punten in een vervolgafspraak.""",
            
            "adviesmotivatie_aow": """
            Er is onvoldoende informatie beschikbaar voor een AOW/pensioenadvies.
            
            Benodigde informatie:
            - Huidige pensioenopbouw
            - Gewenste situatie na pensionering
            - AOW-leeftijd en planning
            - Vermogensopbouw wensen
            
            Advies: Plan een pensioenanalyse gesprek."""
        }
        return defaults.get(section, "Geen informatie beschikbaar voor deze sectie.")