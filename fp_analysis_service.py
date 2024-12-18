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
            initial_analysis = self._extract_key_information(transcript, klantprofiel)
            
            # Second pass: Identify missing information
            missing_info = self._identify_missing_information(initial_analysis)
            
            # Third pass: Generate section drafts
            section_drafts = self._generate_section_drafts(initial_analysis)
            
            return {
                "analysis": initial_analysis,
                "missing_info": missing_info,
                "section_drafts": section_drafts,
                "graphs_needed": self._determine_required_graphs(initial_analysis)
            }
                
        except Exception as e:
            logger.error(f"Error in initial analysis: {str(e)}")
            return self._get_default_analysis()

    def _extract_key_information(self, transcript: str, klantprofiel: str) -> Dict[str, Any]:
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
            
            response = self.llm.invoke(messages)
            logger.info(f"Response content: {response.content}")  # Added logging
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

    def _generate_section_drafts(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate initial drafts for each report section."""
        drafts = {}
        
        for section in self.config.MANDATORY_SECTIONS.keys():
            draft = self._generate_section_content(section, analysis)
            if draft:
                drafts[section] = draft
                
        return drafts

    def _generate_section_content(self, section: str, analysis: Dict[str, Any]) -> Optional[str]:
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
            
            response = self.llm.invoke(messages)
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
                section_content = self._generate_final_section_content(
                    section, 
                    analysis, 
                    app_state.structured_qa_history
                )
                if section_content:
                    report[section] = section_content
            
            return report
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")

            return self._get_default_report()

    def _generate_final_section_content(self, section: str, analysis: Dict[str, Any], qa_history: List[Dict[str, Any]]) -> Optional[str]:
        """Generate final content for a section."""
        try:
            # Implement the logic to generate final section content
            # This is a placeholder implementation
            return analysis.get("section_drafts", {}).get(section, "")
        except Exception as e:
            logger.error(f"Error generating final section content: {str(e)}")
            return None

    async def analyze_transcript(self, transcript: str, app_state: Optional['AppState'] = None) -> Optional[Dict[str, str]]:
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
            validated_sections = self._validate_sections(sections, checklist_analysis["missing_info"])
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
                missing_info=json.dumps(analysis["missing_info"], ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"Error creating enhanced prompt: {str(e)}")
            return None

    def _generate_content(self, formatted_prompt: str) -> Optional[Any]:
        """Generates enhanced content using the LLM."""
        try:
            system_message = """Je bent een ervaren hypotheekadviseur die gespreksnotities en klantinformatie verwerkt tot professionele rapportages.

BELANGRIJKE EISEN:
1. Schrijf uitgebreide, gedetailleerde secties
2. Elk onderdeel moet minimaal 3 paragrafen bevatten
3. Gebruik duidelijke nummeringen (1., 2., 3.)
4. Zorg voor voldoende diepgang en detail
5. Gebruik concrete informatie uit het transcript

STRUCTUUR PER SECTIE:
- Begin met een inleidende alinea
- Gebruik genummerde hoofdsecties (1., 2., 3.)
- Minimaal 3 paragrafen per hoofdsectie
- Eindig met een duidelijke conclusie"""

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=formatted_prompt)
            ]
            
            # Increase temperature slightly for more detailed output
            response = self.llm.invoke(
                messages,
                temperature=0.4,
                max_tokens=4000
            )
            
            if not response or not response.content.strip():
                logger.error("Empty response from LLM")
                return None
                
            return response
                
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return None

    def _get_enhanced_system_prompt(self) -> str:
        return """Je bent een ervaren hypotheekadviseur die gespreksnotities verwerkt tot professionele rapportages.

KWALITEITSEISEN VOOR ALLE SECTIES:
- Schrijf in volledige, vloeiende zinnen
- Gebruik professionele financiële terminologie
- Maak logische verbanden tussen informatie
- Zorg voor consistente diepgang in alle onderdelen
- Gebruik concrete cijfers en details uit de bronnen

STRUCTUUR PER SECTIE:
1. Begin met een duidelijke inleiding
   - Schets de context
   - Geef het doel van de analyse
   - Verwijs naar de specifieke situatie

2. Hoofdonderdelen (minimaal drie)
   - Begin elk onderdeel met een duidelijke titel
   - Werk informatie uit in volledige alinea's
   - Verbind feiten met analyse
   - Onderbouw keuzes en adviezen

3. Afronding
   - Vat belangrijkste punten samen
   - Trek duidelijke conclusies
   - Relateer aan klantdoelen

AANDACHTSPUNTEN:
- Vermijd bullet points
- Geen verwijzingen naar toekomstige gesprekken
- Geen adviseursnamen of datums
- Integreer alle relevante informatie uit transcript en klantprofiel
- Maak financiële impact concreet met cijfers"""

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
            formatted_content = self._format_section_content(content, section)
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

    def _format_section_content(self, content: str, current_section: str) -> str:
        section_template = HYPOTHEEK_TEMPLATES.get(current_section)
        if not section_template:
            return self._format_generic_content(content)
        
        # Extract values from content
        values = self._extract_values_from_content(content)
        
        try:
            formatted_content = section_template.format(**values)
            return formatted_content
        except KeyError as e:
            logger.error(f"Missing value in template: {str(e)}")
            return self._format_generic_content(content)

    def _create_missing_content_notice(self, section: str) -> str:
        section_names = {
            "adviesmotivatie_leningdeel": "de hypothecaire financiering",
            "adviesmotivatie_werkloosheid": "het werkloosheidsscenario",
            "adviesmotivatie_aow": "de pensioen- en AOW-situatie"
        }
        
        section_name = section_names.get(section, section)
        
        return f"""1. Inventarisatie
    Op basis van het gesprek is een eerste analyse gemaakt van {section_name}. De algemene uitgangspunten en wensen zijn besproken.
    
    2. Beschikbare Informatie
    De financiële kaders en persoonlijke voorkeuren zijn geïnventariseerd. Deze vormen de basis voor verdere uitwerking van de mogelijkheden.
    
    3. Analyse
    De besproken opties worden verder uitgewerkt op basis van de specifieke situatie en wensen. De impact van verschillende scenario's wordt daarbij in kaart gebracht."""

    def _format_werkloosheid_section(self, client_info: Dict[str, Any]) -> str:
        """Creates a professionally formatted werkloosheid section."""
        return f"""
Op basis van de besproken situatie is een uitgebreide risicoanalyse uitgevoerd met betrekking tot mogelijke werkloosheid. Deze analyse beschouwt de impact op de financiële situatie en de mogelijke beschermingsmaatregelen.

1. Huidige Situatie
De financiële uitgangspositie is stabiel, met een gezamenlijk netto inkomen van {client_info.get('inkomen', '6.500')} euro per maand voor beide partners. Dit biedt een solide basis voor de hypotheeklasten. Tijdens het gesprek is de mogelijkheid van een werkloosheidsverzekering besproken om de hypotheeklasten van {client_info.get('hypotheeklasten', '1.300')} euro per maand te waarborgen. Er is specifiek gekeken naar een verzekeringsdekking van {client_info.get('dekking', '500')} euro per maand.

2. Risicoanalyse
Een belangrijk aspect van de financiële planning is de impact van mogelijk inkomensverlies door werkloosheid. Dit kan significante gevolgen hebben voor het besteedbaar inkomen en daarmee de mogelijkheid om de hypotheeklasten te dragen. De besproken werkloosheidsverzekering biedt een buffer om deze financiële impact te beperken. De klanten hebben aangegeven positief te staan tegenover het verzekeren van dit risico om de financiële stabiliteit te waarborgen.

3. Advies en Aandachtspunten
De verzekering biedt concrete bescherming tegen inkomensverlies bij werkloosheid. Dit past bij de wens om financiële zekerheid te creëren rond de hypotheekverplichtingen. De voorgestelde dekking van {client_info.get('dekking', '500')} euro per maand vormt een substantiële aanvulling op eventuele werkloosheidsuitkeringen, waardoor de continuïteit van de hypotheekbetalingen beter gewaarborgd is."""

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
        try:
            if not sections:
                logger.warning("No sections provided for quality verification")
                return False
                
            for section_name, content in sections.items():
                # Check for minimum content
                if not content or len(content.split()) < 50:
                    logger.warning(f"Section {section_name} has insufficient content length")
                    return False
                
                # Check for minimum structure
                if not any(marker in content for marker in ['1.', '2.', '3.']):
                    logger.warning(f"Section {section_name} missing required structure (numbered sections)")
                    return False
                
                # Check for proper formatting
                if len(content.split('\n\n')) < 3:
                    logger.warning(f"Section {section_name} lacks proper paragraph separation")
                    return False

            return True
                
        except Exception as e:
            logger.error(f"Error in content quality verification: {str(e)}")
            return False

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
        section_names = {
            "adviesmotivatie_leningdeel": "de hypothecaire financiering",
            "adviesmotivatie_werkloosheid": "het werkloosheidsscenario",
            "adviesmotivatie_aow": "de pensioen- en AOW-situatie"
        }
        
        section_name = section_names.get(section, section)
        
        return f"""1. Inventarisatie
    Op basis van het gesprek is een eerste analyse gemaakt van {section_name}. De algemene uitgangspunten en wensen zijn besproken.
    
    2. Beschikbare Informatie
    De financiële kaders en persoonlijke voorkeuren zijn geïnventariseerd. Deze vormen de basis voor verdere uitwerking van de mogelijkheden.
    
    3. Analyse
    De besproken opties worden verder uitgewerkt op basis van de specifieke situatie en wensen. De impact van verschillende scenario's wordt daarbij in kaart gebracht."""

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

        notice = f"\nAspecten voor {section_titles.get(section_key, section_key)}:"
        for item in missing_items:
            notice += f"\n• {item}"

        return notice
