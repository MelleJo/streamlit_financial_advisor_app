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
            
            # Initialize sections
            sections = {
                "adviesmotivatie_leningdeel": [],
                "adviesmotivatie_werkloosheid": [],
                "adviesmotivatie_aow": []
            }
            
            # Parse sections using list accumulation
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('<adviesmotivatie_'):
                    tag = line.strip('<>')
                    if tag in sections:
                        current_section = tag
                elif line.startswith('</adviesmotivatie_'):
                    current_section = None
                elif current_section and current_section in sections:
                    sections[current_section].append(line)
            
            # Convert accumulated lists to strings
            result = {}
            for section, lines in sections.items():
                if lines:  # Only include sections that have content
                    result[section] = '\n'.join(lines)
                else:
                    result[section] = "Geen informatie beschikbaar voor deze sectie."
            
            # Verify we have all required sections
            if len(result) != 3:
                return self._get_default_analysis_response("Incomplete analyse")
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return self._get_default_analysis_response(f"Error: {str(e)}")

    def _get_default_analysis_response(self, error_msg: str) -> Dict[str, str]:
        """Returns a default analysis response."""
        return {
            "adviesmotivatie_leningdeel": f"Er is een fout opgetreden bij de analyse: {error_msg}",
            "adviesmotivatie_werkloosheid": f"Er is een fout opgetreden bij de analyse: {error_msg}",
            "adviesmotivatie_aow": f"Er is een fout opgetreden bij de analyse: {error_msg}"
        }