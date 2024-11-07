import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
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
        
        # Initial analysis prompt
        self.initial_analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die een initiële analyse uitvoert.
            Identificeer ontbrekende informatie voor een volledig hypotheekadvies."""),
            HumanMessage(content="""
            Analyseer dit transcript en identificeer ontbrekende informatie:
            {transcript}
            
            Retourneer de analyse in dit format:
            {
                "missing_info": {
                    "leningdeel": ["ontbrekend item 1", "ontbrekend item 2"],
                    "werkloosheid": ["ontbrekend item 1", "ontbrekend item 2"],
                    "aow": ["ontbrekend item 1", "ontbrekend item 2"]
                }
            }
            """)
        ])
        
        # Full analysis prompt
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die adviesnotities analyseert. 
            Focus op concrete details en cijfers in je analyse."""),
            HumanMessage(content="""
            Transcript van de adviesnotitie:
            {transcript}

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

    def get_default_response(self, error_msg: str = "") -> Dict[str, str]:
        """Returns a default response structure with optional error message."""
        prefix = "Er is een fout opgetreden bij de analyse" if error_msg else "Er is onvoldoende informatie beschikbaar"
        message = f"{prefix}: {error_msg}" if error_msg else prefix
        
        return {
            "adviesmotivatie_leningdeel": message + "\n\nBenodigd voor leningdeel analyse:\n- Leningbedrag\n- NHG keuze\n- Rentevaste periode\n- Hypotheekvorm",
            "adviesmotivatie_werkloosheid": message + "\n\nBenodigd voor werkloosheid analyse:\n- Huidige arbeidssituatie\n- Risico-inschatting\n- Gewenste dekking",
            "adviesmotivatie_aow": message + "\n\nBenodigd voor AOW analyse:\n- Pensioenleeftijd\n- Pensioenwensen\n- Vermogensopbouw planning"
        }

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript to identify missing information."""
        try:
            if not transcript or len(transcript.strip()) == 0:
                return {
                    "missing_info": {
                        "leningdeel": ["Geen transcript aangeleverd"],
                        "werkloosheid": ["Geen transcript aangeleverd"],
                        "aow": ["Geen transcript aangeleverd"]
                    }
                }

            messages = self.initial_analysis_prompt.format_messages(transcript=transcript)
            response = self.llm.invoke(messages)
            
            content = response.content.strip()
            logger.info(f"Initial analysis response: {content}")
            
            # Parse JSON response
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                result = json.loads(content)
                return result

            except json.JSONDecodeError:
                return {
                    "missing_info": {
                        "leningdeel": ["Error parsing analysis"],
                        "werkloosheid": ["Error parsing analysis"],
                        "aow": ["Error parsing analysis"]
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in initial transcript analysis: {str(e)}")
            return {
                "missing_info": {
                    "leningdeel": ["Error analyzing leningdeel"],
                    "werkloosheid": ["Error analyzing werkloosheid"],
                    "aow": ["Error analyzing aow"]
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
                return self.get_default_response("Geen transcript aangeleverd")

            # Format additional info if available
            additional_info = "Geen aanvullende informatie beschikbaar."
            if app_state and hasattr(app_state, 'additional_info') and app_state.additional_info:
                try:
                    info_parts = []
                    for qa_dict in app_state.additional_info.values():
                        if isinstance(qa_dict, dict):
                            q = qa_dict.get('question', '')
                            a = qa_dict.get('answer', '')
                            if q and a:
                                info_parts.append(f"Vraag: {q}\nAntwoord: {a}")
                    if info_parts:
                        additional_info = "Aanvullende informatie:\n\n" + "\n\n".join(info_parts)
                except Exception as e:
                    logger.error(f"Error formatting additional info: {str(e)}")

            # Get response from LLM
            messages = self.analysis_prompt.format_messages(
                transcript=transcript,
                additional_info=additional_info
            )
            response = self.llm.invoke(messages)
            
            content = response.content
            logger.info(f"Raw LLM response: {content}")
            
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
                    tag = line.strip('<>')
                    if tag in sections:
                        current_section = tag
                elif line.startswith('</adviesmotivatie_'):
                    current_section = None
                elif current_section and current_section in sections:
                    sections[current_section].append(line)
            
            # Convert to final format
            result = {}
            for section, lines in sections.items():
                if lines:
                    result[section] = '\n'.join(lines)
                else:
                    result[section] = f"Geen informatie beschikbaar voor {section}"
            
            # Verify all sections are present
            if len(result) != 3:
                return self.get_default_response("Incomplete analyse")
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return self.get_default_response(str(e))