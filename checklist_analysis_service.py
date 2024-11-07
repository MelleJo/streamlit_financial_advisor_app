"""
File: checklist_analysis_service.py
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import logging

logger = logging.getLogger(__name__)

class ChecklistAnalysisService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=api_key
        )

    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the transcript for missing information based on the checklist."""
        
        system_prompt = """Je bent een ervaren hypotheekadviseur die transcripten analyseert.
        Je taak is om te controleren welke verplichte onderdelen van het hypotheekadvies ontbreken.
        
        Geef ALLEEN een JSON response met ontbrekende punten. Als een onderwerp voldoende behandeld is,
        neem je het NIET op in de response.
        
        Controleer de volgende punten:
        
        Leningdeel:
        - Leningbedrag en onderbouwing
        - NHG keuze en motivatie
        - Rentevaste periode met onderbouwing
        - Hypotheekvorm met uitleg
        - Fiscale aspecten en gevolgen
        - Maandlasten berekening
        
        Werkloosheid:
        - Huidige arbeidssituatie
        - Werkloosheidsrisico inschatting
        - Wensen bij werkloosheid
        - Benodigde dekking en verzekeringen
        - Impact op maandlasten
        
        AOW:
        - AOW-leeftijd en planning
        - Hypotheeksituatie bij AOW
        - Pensioenopbouw en inkomen
        - Wensen na pensionering
        - Vermogensopbouw planning"""

        user_prompt = f"""
        Analyseer dit transcript en geef aan welke VERPLICHTE onderdelen nog ontbreken:
        
        {transcript}
        
        Geef je antwoord in precies dit JSON format:
        {{
            "missing_topics": {{
                "leningdeel": [],  // lijst van ontbrekende punten
                "werkloosheid": [],
                "aow": []
            }},
            "explanation": "" // korte uitleg waarom deze punten ontbreken
        }}
        
        BELANGRIJK:
        - Include een categorie ALLEEN als er echt iets ontbreekt
        - Als alles behandeld is in een categorie, laat die categorie dan leeg
        - Wees streng maar redelijk - als iets impliciet duidelijk is hoeft het niet als ontbrekend gemarkeerd te worden
        """

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])

            response = self.llm(prompt.format_messages())
            content = response.content
            
            # Remove any markdown formatting if present
            content = content.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(content)
            
            # Filter out empty categories
            result['missing_topics'] = {
                k: v for k, v in result['missing_topics'].items() 
                if v
            }
            
            return result

        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            return {
                "missing_topics": {},
                "explanation": "Er is een fout opgetreden bij de analyse."
            }