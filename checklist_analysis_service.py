"""
File: checklist_analysis_service.py
Handles intelligent analysis of mortgage advice transcripts using gpt-4o-mini.
"""
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECKLIST = {
    "leningdeel": {
        "title": "Leningdeel",
        "required": [
            "Exacte leningbedrag met onderbouwing",
            "NHG keuze en onderbouwing",
            "Maandlasten berekening",
            "Rentevaste periode met motivatie",
            "Hypotheekvorm met toelichting",
            "Fiscale aspecten en voordelen"
        ]
    },
    "werkloosheid": {
        "title": "Werkloosheid",
        "required": [
            "Huidige arbeidssituatie",
            "Werkloosheidsrisico analyse",
            "WW-uitkering en duur",
            "Impact op maandlasten",
            "Verzekeringswensen en dekking"
        ]
    },
    "aow": {
        "title": "AOW en Pensioen",
        "required": [
            "AOW-leeftijd en planning",
            "Hypotheeksituatie bij pensionering",
            "Pensioeninkomen en opbouw",
            "Toekomstperspectief na AOW",
            "Vermogensplanning"
        ]
    }
}

class ChecklistAnalysisService:
    def __init__(self, api_key: str):
        """Initialize the service with OpenAI API key."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=api_key
        )
        self.checklist = CHECKLIST

    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Analyzes the transcript against the checklist requirements.
        
        Args:
            transcript (str): The mortgage advice transcript to analyze
            
        Returns:
            Dict containing missing topics and explanation
        """
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided")
            return self._get_default_response("Geen transcript aangeleverd")

        try:
            system_message = {
                "role": "system",
                "content": """Je bent een ervaren hypotheekadviseur die transcripten analyseert op volledigheid.
                Je controleert of alle verplichte onderdelen van een hypotheekadvies aanwezig zijn.
                
                Als een onderwerp voldoende behandeld is, ook IMPLICIET, dan is dat goed.
                Wees kritisch maar realistisch - niet elk detail hoeft expliciet genoemd te worden.
                
                Geef je antwoord ALLEEN in het gevraagde JSON format.
                GEEN extra tekst, uitleg of markdown."""
            }

            user_message = {
                "role": "user",
                "content": f"""
                Analyseer dit hypotheekadvies transcript en identificeer welke verplichte onderdelen ontbreken:

                TRANSCRIPT:
                {transcript}

                VERPLICHTE ONDERDELEN:
                {json.dumps(self.checklist, indent=2, ensure_ascii=False)}

                Geef je antwoord in exact dit JSON format:
                {{
                    "missing_topics": {{
                        "leningdeel": ["ontbrekend punt 1", "ontbrekend punt 2"],
                        "werkloosheid": ["ontbrekend punt 3"],
                        "aow": ["ontbrekend punt 4"]
                    }},
                    "explanation": "Korte uitleg waarom deze punten ontbreken"
                }}
                
                Regels:
                - Alleen ECHT ontbrekende punten opnemen
                - Als een categorie compleet is, geef dan een lege lijst
                - Als iets impliciet duidelijk is, niet als ontbrekend markeren
                """
            }

            response = self.llm.invoke([system_message, user_message])
            content = response.content.strip()
            
            # Clean up any markdown or formatting
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw content: {content}")
                return self._get_default_response("Fout bij het verwerken van de analyse")

            # Validate and clean the response
            if not isinstance(result, dict):
                return self._get_default_response("Ongeldig antwoordformaat")
            
            missing_topics = result.get('missing_topics', {})
            explanation = result.get('explanation', '')

            # Filter out empty categories and invalid items
            cleaned_topics = {}
            for category, items in missing_topics.items():
                if category in self.checklist and isinstance(items, list):
                    valid_items = [item for item in items if isinstance(item, str) and item.strip()]
                    if valid_items:
                        cleaned_topics[category] = valid_items

            return {
                "missing_topics": cleaned_topics,
                "explanation": explanation if isinstance(explanation, str) else ""
            }

        except Exception as e:
            logger.exception("Error analyzing transcript")
            return self._get_default_response(f"Analysefout: {str(e)}")

    def get_checklist(self) -> Dict[str, Any]:
        """Returns the complete checklist structure."""
        return self.checklist

    def _get_default_response(self, explanation: str) -> Dict[str, Any]:
        """Returns a default response with basic missing items."""
        return {
            "missing_topics": {
                "leningdeel": ["Basisinformatie ontbreekt"],
                "werkloosheid": ["Risico-analyse ontbreekt"],
                "aow": ["Toekomstplanning ontbreekt"]
            },
            "explanation": explanation
        }

    def validate_coverage(self, transcript: str, section: str) -> Dict[str, Any]:
        """
        Validates the coverage of a specific section of the checklist.
        
        Args:
            transcript (str): The transcript to analyze
            section (str): The section to validate (leningdeel, werkloosheid, or aow)
            
        Returns:
            Dict containing coverage analysis
        """
        if section not in self.checklist:
            return {"error": "Ongeldige sectie"}

        try:
            required_points = self.checklist[section]["required"]
            
            system_message = {
                "role": "system",
                "content": f"""Analyseer dit transcript specifiek voor de sectie '{section}'.
                Check elk van deze punten: {json.dumps(required_points, ensure_ascii=False)}
                Geef aan welke punten voldoende behandeld zijn en welke ontbreken."""
            }

            user_message = {
                "role": "user",
                "content": f"""
                TRANSCRIPT:
                {transcript}
                
                Geef je antwoord in dit JSON format:
                {{
                    "covered": ["punt 1", "punt 2"],
                    "missing": ["punt 3"],
                    "partial": ["punt 4"],
                    "explanation": "Toelichting hier"
                }}"""
            }

            response = self.llm.invoke([system_message, user_message])
            content = response.content.strip()
            content = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(content)

        except Exception as e:
            logger.error(f"Error validating section {section}: {e}")
            return {
                "error": f"Validatiefout: {str(e)}",
                "section": section
            }
    def validate_audio(self, audio_bytes):
        """Validate the recorded audio data"""
        if not audio_bytes:
            return False
            
        try:
            # Check minimum size (1KB)
            min_size = 1024
            if len(audio_bytes) < min_size:
                logger.warning(f"Audio file too small: {len(audio_bytes)} bytes")
                return False
                
            # Additional validation could be added here
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio: {str(e)}")
            return False