import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    """Configuration for FP analysis"""
    MANDATORY_SECTIONS = {
        "samenvatting": ["netto_besteedbaar_inkomen", "doelstellingen", "kernadvies"],
        "huidige_situatie": ["inkomen", "uitgaven", "vermogen", "schulden"],
        "pensioen": ["aow", "pensioenopbouw", "lijfrente", "doelvermogen"],
        "overlijden": ["inkomensterugval", "voorzieningen", "verzekeringen"],
        "arbeidsongeschiktheid": ["inkomensterugval", "voorzieningen", "verzekeringen"],
        "werkloosheid": ["ww_rechten", "voorzieningen", "overbrugging"],
        "vermogen": ["sparen", "beleggen", "erfenis", "schenking"]
    }
    
    GRAPH_REQUIREMENTS = {
        "huidige_situatie": ["inkomsten_uitgaven_balans", "vermogensopbouw"],
        "pensioen": ["pensioeninkomen_prognose", "doelvermogen_analyse"],
        "overlijden": ["inkomen_vergelijking", "kapitaalbehoefte"],
        "arbeidsongeschiktheid": ["inkomen_vergelijking", "uitkeringsniveaus"],
        "vermogen": ["vermogensgroei", "vermogensverdeling"]
    }

class FPAnalysisService:
    def __init__(self, api_key: str):
        """Initialize the service with enhanced capabilities."""
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            openai_api_key=api_key
        )
        self.config = AnalysisConfig()
        
    async def analyze_input(self, transcript: str, klantprofiel: str) -> Dict[str, Any]:
        """Analyze transcript and klantprofiel to generate initial assessment."""
        try:
            # First pass: Extract key information
            initial_analysis = await self._extract_key_information(transcript, klantprofiel)
            
            # Second pass: Identify missing information
            missing_info = self._identify_missing_information(initial_analysis)
            
            # Third pass: Generate section drafts
            section_drafts = await self._generate_section_drafts(initial_analysis)
            
            return {
                "analysis": initial_analysis,
                "missing_info": missing_info,
                "section_drafts": section_drafts,
                "graphs_needed": self._determine_required_graphs(initial_analysis)
            }
                
        except Exception as e:
            logger.error(f"Error in initial analysis: {str(e)}")
            return self._get_default_analysis()

    async def _extract_key_information(self, transcript: str, klantprofiel: str) -> Dict[str, Any]:
        """Extract key information from input sources."""
        try:
            messages = [
                SystemMessage(content="""Je bent een ervaren financieel planner die klantgesprekken analyseert.
Extraheer alle relevante informatie voor een financieel plan uit het transcript en klantprofiel.
Focus op concrete cijfers, wensen en doelstellingen."""),
                HumanMessage(content=f"""
Analyseer deze input voor een financieel plan:

TRANSCRIPT:
{transcript}

KLANTPROFIEL:
{klantprofiel}

Geef je antwoord in dit JSON format:
{{
    "netto_besteedbaar_inkomen": {{
        "huidig": "bedrag",
        "toelichting": "uitleg"
    }},
    "doelstellingen": ["doel1", "doel2"],
    "pensioen": {{
        "huidige_opbouw": "details",
        "wensen": "beschrijving"
    }},
    "risicos": {{
        "overlijden": "analyse",
        "ao": "analyse",
        "werkloosheid": "analyse"
    }},
    "vermogen": {{
        "huidig": "bedrag",
        "planning": "beschrijving"
    }}
}}""")
            ]
            
            response = await self.llm.invoke(messages)
            return json.loads(response.content)
                
        except Exception as e:
            logger.error(f"Error extracting key information: {str(e)}")
            return {}
    
    def _identify_missing_information(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify missing mandatory information per section."""
        missing_info = {}
        
        for section, required_fields in self.config.MANDATORY_SECTIONS.items():
            missing_fields = []
            section_data = analysis.get(section, {})
            
            for field in required_fields:
                if not self._check_field_completeness(section_data, field):
                    missing_fields.append(field)
            
            if missing_fields:
                missing_info[section] = missing_fields
                
        return missing_info

    def _check_field_completeness(self, data: Dict[str, Any], field: str) -> bool:
        """Check if a field contains sufficient information."""
        if field not in data:
            return False
            
        value = data[field]
        if isinstance(value, str):
            return bool(value.strip())
        elif isinstance(value, (list, dict)):
            return bool(value)
        return False

    async def _generate_section_drafts(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate initial drafts for each report section."""
        drafts = {}
        
        for section in self.config.MANDATORY_SECTIONS.keys():
            draft = await self._generate_section_content(section, analysis)
            if draft:
                drafts[section] = draft
                
        return drafts

    async def _generate_section_content(self, section: str, analysis: Dict[str, Any]) -> Optional[str]:
        """Generate content for a specific section using standard texts as templates."""
        try:
            messages = [
                SystemMessage(content=f"""Je bent een ervaren financieel planner die een {section} rapport schrijft.
Gebruik de standaard teksten als basis, maar pas ze aan op basis van de specifieke klantsituatie.
Zorg voor concrete cijfers en persoonlijke details waar mogelijk."""),
                HumanMessage(content=f"""
ANALYSE:
{json.dumps(analysis, ensure_ascii=False)}

Genereer een professionele tekst voor de {section} sectie.
Gebruik concrete cijfers en details uit de analyse.
Volg de structuur van de standaard teksten maar personaliseer de inhoud.""")
            ]
            
            response = await self.llm.invoke(messages)
            return response.content.strip()
                
        except Exception as e:
            logger.error(f"Error generating section content: {str(e)}")
            return None

    def _determine_required_graphs(self, analysis: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Determine which graphs should be included in each section."""
        graphs_needed = {}
        
        for section, graph_types in self.config.GRAPH_REQUIREMENTS.items():
            section_graphs = []
            for graph_type in graph_types:
                if self._should_include_graph(section, graph_type, analysis):
                    section_graphs.append({
                        "type": graph_type,
                        "title": self._get_graph_title(graph_type),
                        "data_requirements": self._get_graph_data_requirements(graph_type)
                    })
            if section_graphs:
                graphs_needed[section] = section_graphs
                    
        return graphs_needed

    def _should_include_graph(self, section: str, graph_type: str, analysis: Dict[str, Any]) -> bool:
        """Determine if a specific graph should be included based on available data."""
        section_data = analysis.get(section, {})
        
        # Define minimum data requirements for each graph type
        requirements = {
            "inkomsten_uitgaven_balans": ["inkomen", "uitgaven"],
            "vermogensopbouw": ["vermogen", "planning"],
            "pensioeninkomen_prognose": ["pensioen", "inkomen"],
            "doelvermogen_analyse": ["vermogen", "doelstellingen"],
            "inkomen_vergelijking": ["inkomen", "risicos"],
            "kapitaalbehoefte": ["risicos", "vermogen"],
            "vermogensgroei": ["vermogen", "planning"],
            "vermogensverdeling": ["vermogen"]
        }
        
        required_fields = requirements.get(graph_type, [])
        return all(field in section_data for field in required_fields)

    def _get_graph_title(self, graph_type: str) -> str:
        """Get the appropriate title for a graph type."""
        titles = {
            "inkomsten_uitgaven_balans": "Inkomsten en Uitgaven Overzicht",
            "vermogensopbouw": "Vermogensopbouw Prognose",
            "pensioeninkomen_prognose": "Pensioeninkomen Prognose",
            "doelvermogen_analyse": "Doelvermogen Analyse",
            "inkomen_vergelijking": "Inkomensvergelijking Scenario's",
            "kapitaalbehoefte": "Kapitaalbehoefte Analyse",
            "vermogensgroei": "Vermogensgroei Projectie",
            "vermogensverdeling": "Vermogensverdeling Overzicht"
        }
        return titles.get(graph_type, graph_type.replace("_", " ").title())

    def _get_graph_data_requirements(self, graph_type: str) -> Dict[str, str]:
        """Get the data requirements for a specific graph type."""
        requirements = {
            "inkomsten_uitgaven_balans": {
                "x_axis": "Maanden",
                "y_axis": "Bedrag (€)",
                "series": ["Inkomsten", "Uitgaven"]
            },
            "vermogensopbouw": {
                "x_axis": "Jaren",
                "y_axis": "Vermogen (€)",
                "series": ["Totaal Vermogen", "Doelvermogen"]
            },
            "pensioeninkomen_prognose": {
                "x_axis": "Leeftijd",
                "y_axis": "Inkomen (€)",
                "series": ["Benodigd", "Verwacht"]
            }
        }
        return requirements.get(graph_type, {})

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis structure when processing fails."""
        return {
            "analysis": {},
            "missing_info": {section: fields for section, fields in self.config.MANDATORY_SECTIONS.items()},
            "section_drafts": {},
            "graphs_needed": {}
        }

    async def generate_report(self, analysis: Dict[str, Any], app_state: Any) -> Dict[str, Any]:
        """Generate the final report based on analysis and app state."""
        try:
            report = {}
            
            for section in self.config.MANDATORY_SECTIONS.keys():
                section_content = await self._generate_final_section_content(
                    section, 
                    analysis, 
                    app_state.structured_qa_history
                )
                if section_content:
                    report[section] = section_content
            
            return report
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {}
