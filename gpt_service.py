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

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript to identify missing information."""
        try:
            messages = self.initial_analysis_prompt.format_messages(transcript=transcript)
            response = self.llm.invoke(messages)
            
            content = response.content
            logger.info(f"Initial analysis response: {content}")
            
            # Parse JSON response
            try:
                # Clean the response if it contains markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                return json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response")
                return {
                    "missing_info": {
                        "leningdeel": ["Kon leningdeel informatie niet analyseren"],
                        "werkloosheid": ["Kon werkloosheid informatie niet analyseren"],
                        "aow": ["Kon AOW informatie niet analyseren"]
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in initial transcript analysis: {str(e)}")
            return {
                "missing_info": {
                    "leningdeel": ["Error analyzing leningdeel information"],
                    "werkloosheid": ["Error analyzing werkloosheid information"],
                    "aow": ["Error analyzing AOW information"]
                }
            }

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
            
            # Parse sections using dictionary comprehension
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