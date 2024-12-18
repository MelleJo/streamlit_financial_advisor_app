import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
import json
from app_state import AppState
from templates import FP_TEMPLATES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FPService:
    def __init__(self, api_key: str):
        """Initialize the FP service with required dependencies."""
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            openai_api_key=api_key
        )
        
        # FP report sections and required fields
        self.report_sections = {
            "samenvatting": ["netto_besteedbaar_inkomen", "hoofdpunten", "kernadvies"],
            "uitwerking_advies": ["bevindingen", "aanbevelingen"],
            "huidige_situatie": ["situatie_beschrijving", "analyse"],
            "situatie_later": ["pensioen", "aow", "vermogen"],
            "situatie_overlijden": ["verzekeringen", "voorzieningen"],
            "situatie_arbeidsongeschiktheid": ["verzekeringen", "voorzieningen"],
            "erven_schenken": ["planning", "mogelijkheden"],
            "actiepunten": ["client", "veldhuis"]
        }

    async def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyze the initial transcript for FP report."""
        try:
            system_message = {
                "role": "system",
                "content": """Je bent een ervaren financieel adviseur die transcripten analyseert voor financiële planning.
Extraheer de belangrijkste informatie en structureer deze volgens het gevraagde format."""
            }

            user_message = {
                "role": "user",
                "content": f"""
Analyseer dit transcript voor een financieel plan:

{transcript}

Geef je antwoord in dit JSON format:
{{
    "netto_besteedbaar_inkomen": "bedrag + toelichting",
    "hoofdpunten": ["punt 1", "punt 2", "punt 3"],
    "kernadvies": "korte samenvatting van het advies"
}}"""
            }

            response = await self.llm.invoke([system_message, user_message])
            content = response.content.strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                return self._get_default_analysis()

        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return self._get_default_analysis()

    async def process_advisor_recording(self, audio_bytes: bytes, section: str) -> Optional[Dict[str, Any]]:
        """Process an advisor's recording for a specific FP report section."""
        try:
            # Hier zou normaal gesproken de audio worden getranscribeerd, maar voor nu retourneren we een placeholder
            # totdat we integreren met de transcriptieservice
            return {
                "content": "Sectie nog te verwerken",
                "graphs": None
            }

        except Exception as e:
            logger.error(f"Error processing advisor recording: {str(e)}")
            return None

    async def generate_fp_report(self, app_state: AppState) -> Dict[str, Any]:
        """Generate the complete FP report based on all collected information."""
        try:
            return {
                "samenvatting": await self._format_section_content(app_state.fp_state.samenvatting, "samenvatting"),
                "uitwerking_advies": app_state.fp_state.uitwerking_advies,
                "huidige_situatie": app_state.fp_state.huidige_situatie,
                "situatie_later": app_state.fp_state.situatie_later,
                "situatie_overlijden": app_state.fp_state.situatie_overlijden,
                "situatie_arbeidsongeschiktheid": app_state.fp_state.situatie_arbeidsongeschiktheid,
                "erven_schenken": app_state.fp_state.erven_schenken,
                "actiepunten": app_state.fp_state.actiepunten
            }
        except Exception as e:
            logger.error(f"Error generating FP report: {str(e)}")
            return self._get_default_report()

    async def _format_section_content(self, content: str, section: str) -> str:
        """Format the section content using templates."""
        section_template = FP_TEMPLATES.get(section)
        if not section_template:
            return content
        
        # Extract values from content
        values = self._extract_values_from_content(content)
        
        try:
            formatted_content = section_template.format(**values)
            return formatted_content
        except KeyError as e:
            logger.error(f"Missing value in template: {str(e)}")
            return content

    def _extract_values_from_content(self, content: str) -> Dict[str, Any]:
        """Extract values from the section content."""
        # Placeholder voor het extraheren van waarden uit de inhoud
        # Dit moet worden geïmplementeerd op basis van de werkelijke inhoudsstructuur
        return {}

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis structure when processing fails."""
        return {
            "netto_besteedbaar_inkomen": "Nog te bepalen",
            "hoofdpunten": ["Geen informatie beschikbaar"],
            "kernadvies": "Meer informatie nodig voor analyse"
        }

    def _get_default_report(self) -> Dict[str, Any]:
        """Return default report structure when generation fails."""
        return {section: {"content": "Informatie niet beschikbaar", "graphs": None}
                for section in self.report_sections}
