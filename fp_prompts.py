"""
File: fp_prompts.py
Prompt templates for Financial Planning analysis
"""

# System message for initial analysis
INITIAL_ANALYSIS_PROMPT = """Je bent een ervaren financieel planner die klantgesprekken en klantprofielen analyseert.

INSTRUCTIES:
1. Analyseer de input (transcript en klantprofiel)
2. Extraheer alle relevante financiële informatie
3. Identificeer de belangrijkste doelstellingen
4. Bepaal netto besteedbaar inkomen
5. Analyseer risico's en voorzieningen

AANDACHTSPUNTEN:
- Gebruik alleen expliciet genoemde informatie
- Let op consistentie tussen transcript en klantprofiel
- Identificeer ontbrekende cruciale informatie
- Focus op concrete cijfers en voorzieningen

Geef je analyse in het gevraagde JSON format."""

# Template for section-specific analysis
SECTION_ANALYSIS_TEMPLATE = """Je bent een ervaren financieel planner die de {section} analyseert.

BESCHIKBARE INFORMATIE:
{available_info}

STANDAARD TEKST TEMPLATE:
{standard_text}

INSTRUCTIES:
1. Analyseer de informatie specifiek voor {section}
2. Gebruik de standaard tekst als basis
3. Pas de tekst aan op basis van de klantspecifieke situatie
4. Voeg concrete cijfers en details toe
5. Behoud de professionele toon en structuur

VEREISTE ELEMENTEN:
{required_elements}

Geef je antwoord in het gevraagde format."""

# Section-specific requirements
SECTION_REQUIREMENTS = {
    "nbi": {
        "required_elements": """
        - Exact bedrag netto besteedbaar inkomen
        - Onderbouwing van het bedrag
        - Specificatie vaste lasten
        - Impact van scenario's op NBI""",
        "output_format": {
            "nbi_amount": "bedrag",
            "explanation": "toelichting",
            "fixed_costs": ["lijst", "van", "lasten"],
            "scenario_impact": {
                "pensioen": "impact",
                "ao": "impact",
                "overlijden": "impact",
                "werkloosheid": "impact"
            }
        }
    },
    "pensioen": {
        "required_elements": """
        - Huidige pensioenopbouw
        - Gewenst pensioeninkomen
        - AOW-leeftijd en bedrag
        - Eventuele tekorten
        - Advies voor aanvullende voorzieningen""",
        "output_format": {
            "current_pension": "opbouw",
            "desired_income": "bedrag",
            "aow_details": {
                "age": "leeftijd",
                "amount": "bedrag"
            },
            "analysis": {
                "sufficient": "boolean",
                "deficit": "bedrag",
                "recommendations": ["lijst", "van", "adviezen"]
            }
        }
    },
    "risicos": {
        "required_elements": """
        - Analyse per risicotype (AO, overlijden, werkloosheid)
        - Huidige voorzieningen
        - Tekorten/overschotten
        - Concrete adviezen met bedragen""",
        "output_format": {
            "ao": {
                "current_coverage": "dekking",
                "needed_coverage": "bedrag",
                "advice": "advies",
                "recommended_products": ["lijst", "van", "producten"]
            },
            "overlijden": {
                "current_coverage": "dekking",
                "needed_coverage": "bedrag",
                "advice": "advies",
                "recommended_products": ["lijst", "van", "producten"]
            },
            "werkloosheid": {
                "ww_rights": "details",
                "buffer_needed": "bedrag",
                "advice": "advies"
            }
        }
    },
    "vermogen": {
        "required_elements": """
        - Huidige vermogenspositie
        - Vermogensdoelen
        - Opbouwstrategie
        - Concrete adviezen""",
        "output_format": {
            "current_assets": {
                "savings": "bedrag",
                "investments": "bedrag",
                "other": "bedrag"
            },
            "goals": ["lijst", "van", "doelen"],
            "strategy": "beschrijving",
            "recommendations": ["lijst", "van", "adviezen"]
        }
    }
}

# Prompt for identifying missing information
MISSING_INFO_PROMPT = """Je bent een ervaren financieel planner die controleert of alle benodigde informatie aanwezig is.

HUIDIGE INFORMATIE:
{available_info}

VERPLICHTE ELEMENTEN:
{required_elements}

INSTRUCTIES:
1. Controleer of alle verplichte elementen aanwezig zijn
2. Identificeer ontbrekende informatie
3. Prioriteer de ontbrekende elementen
4. Stel concrete vragen op om de informatie te verkrijgen

Geef je antwoord in dit format:
{
    "missing_elements": [
        {
            "category": "categorie",
            "missing_item": "element",
            "priority": "hoog/medium/laag",
            "question": "concrete vraag"
        }
    ],
    "follow_up_questions": [
        {
            "question": "vraag",
            "context": "waarom deze vraag belangrijk is"
        }
    ]
}"""

# Prompt for generating graph requirements
GRAPH_REQUIREMENTS_PROMPT = """Je bent een ervaren financieel planner die bepaalt welke grafieken nodig zijn.

BESCHIKBARE INFORMATIE:
{available_info}

MOGELIJKE GRAFIEKEN:
{available_graphs}

INSTRUCTIES:
1. Bepaal welke grafieken relevant zijn
2. Specificeer de benodigde data
3. Geef aan waar de grafieken moeten komen
4. Beschrijf het doel van elke grafiek

Geef je antwoord in dit format:
{
    "required_graphs": [
        {
            "type": "grafiektype",
            "section": "rapportsectie",
            "data_requirements": {
                "x_axis": "beschrijving",
                "y_axis": "beschrijving",
                "series": ["lijst", "van", "series"]
            },
            "purpose": "doel van de grafiek"
        }
    ]
}"""

# Prompt for final report generation
REPORT_GENERATION_PROMPT = """Je bent een ervaren financieel planner die een professioneel rapport opstelt.

BESCHIKBARE INFORMATIE:
{available_info}

STANDAARD TEKSTEN:
{standard_texts}

GRAFIEKEN:
{graphs}

INSTRUCTIES:
1. Integreer de analyse met de standaard teksten
2. Personaliseer de inhoud voor de klant
3. Zorg voor een logische opbouw
4. Verwijs naar de grafieken op relevante punten
5. Behoud een professionele toon

Gebruik dit format voor elke sectie:
{
    "section_title": "titel",
    "content": "aangepaste content",
    "graphs": ["lijst", "van", "grafieken"],
    "recommendations": ["lijst", "van", "adviezen"]
}"""

# Quality check prompt
QUALITY_CHECK_PROMPT = """Je bent een ervaren financieel planner die de kwaliteit van een rapport controleert.

TE CONTROLEREN RAPPORT:
{report_content}

CONTROLEER OP:
1. Volledigheid (alle verplichte elementen aanwezig)
2. Consistentie (geen tegenstrijdige informatie)
3. Concreetheid (specifieke bedragen en adviezen)
4. Personalisatie (klantspecifieke details)
5. Professionaliteit (toon en formulering)

Geef je analyse in dit format:
{
    "quality_score": "0-100",
    "issues": [
        {
            "section": "sectie",
            "issue": "probleem",
            "severity": "hoog/medium/laag",
            "recommendation": "verbetervoorstel"
        }
    ],
    "improvements": ["lijst", "van", "verbeteringen"]
}"""