"""
File: definitions.py
Contains mortgage-related definitions and explanation enhancement functionality for the AI Hypotheek Assistent.
This module provides:
1. A comprehensive dictionary of mortgage-related terms and their explanations in Dutch,
   covering key concepts like NHG, mortgage types, fixed interest periods, etc.
2. A function to improve explanations by integrating basic definitions into the original
   advice text in a natural and professional way using gpt-4o.
"""
import logging

MORTGAGE_DEFINITIONS = {
    "NHG": """
De Nationale Hypotheek Garantie (NHG) is een garantie op hypotheken. Met NHG bent u verzekerd van een verantwoorde hypotheek die aansluit op uw situatie. Bovendien kunt u met NHG profiteren van een rentevoordeel. Hierdoor zijn uw maandlasten lager.

Voordelen:
- Lagere hypotheekrente
- Bescherming bij onverwachte gebeurtenissen
- Verantwoorde hypotheek
""",

    "annuïteitenhypotheek": """
Bij een annuïteitenhypotheek blijft het maandbedrag gelijk tijdens de rentevaste periode. In het begin betaalt u veel rente en lost u weinig af. Naarmate de looptijd vordert, betaalt u minder rente en lost u meer af.

Kenmerken:
- Gelijkblijvende maandlasten
- Fiscaal voordelig aan het begin
- Geleidelijke opbouw eigendom
""",

    "rentevaste periode": """
De rentevaste periode is de periode waarin uw hypotheekrente gelijk blijft. Hoe langer deze periode, hoe meer zekerheid u heeft over uw maandlasten.

Aandachtspunten:
- Langere periode = hogere rente
- Meer zekerheid over maandlasten
- Bescherming tegen rentestijgingen
""",

    "fiscaal aftrekbaar": """
Hypotheekrente is onder bepaalde voorwaarden fiscaal aftrekbaar. Dit betekent dat u de betaalde hypotheekrente mag aftrekken van uw belastbaar inkomen, waardoor uw netto maandlasten lager uitvallen.

Voorwaarden:
- Eigen woning als hoofdverblijf
- Annuïtair of lineair aflossen
- Maximaal 30 jaar aftrekbaar
""",

    "leningbedrag": """
Het leningbedrag is het bedrag dat u leent voor uw hypotheek. Dit bedrag wordt bepaald door verschillende factoren:

Factoren:
- Inkomen (maximale leencapaciteit)
- Waarde van de woning
- Eigen middelen
- NHG-grens (indien van toepassing)
""",

    "maandlasten": """
Maandlasten zijn de totale kosten die u maandelijks betaalt voor uw hypotheek. Deze bestaan uit:

Componenten:
- Rente
- Aflossing (bij annuïtair of lineair)
- Eventuele verzekeringspremies
- Eventuele bankspaarrekening
""",

    "looptijd": """
De looptijd van een hypotheek is de periode waarin u de hypotheek moet aflossen. De standaard looptijd is 30 jaar.

Kenmerken:
- Maximaal 30 jaar fiscaal aftrekbaar
- Bepalend voor maandlasten
- Kan korter maar meestal niet langer
""",

    "arbeidsongeschiktheid": """
Arbeidsongeschiktheid kan grote financiële gevolgen hebben voor uw hypotheek. Bij 50% arbeidsongeschiktheid en het niet kunnen vinden van passend werk voor de overige 50%, heeft u alleen recht op een WGA-vervolguitkering.

Belangrijke overwegingen:
- Impact op inkomen significant
- WGA-vervolguitkering vaak lager dan regulier inkomen
- Mogelijkheid tot aanvullende verzekering
- Woonlastenverzekering als vangnet
""",

    "woonlastenverzekering": """
Een woonlastenverzekering helpt bij het betalen van uw maandelijkse woonlasten in onverwachte situaties.

Kenmerken:
- Dekking bij arbeidsongeschiktheid of werkloosheid
- Maximale dekking meestal 125% van woonlasten
- Keuze in eigen risicoperiode
- Uitkeringsduur is beperkt (vaak 12-24 maanden)
- Netto uitkering mogelijk
""",

    "werkloosheid": """
Het risico op werkloosheid verdient aandacht bij het afsluiten van een hypotheek. Verschillende factoren bepalen of extra verzekering wenselijk is:

Overwegingen:
- Arbeidsmarktsituatie in uw sector
- Eigen middelen als buffer
- Mogelijke steun partner
- WW-uitkering als tijdelijk vangnet
- Optie tot werkloosheidsverzekering
""",

    "werkloosheidsverzekering": """
Een werkloosheidsverzekering kan financiële zekerheid bieden bij onvrijwillig ontslag.

Aandachtspunten:
- Alleen mogelijk met vast dienstverband
- Dekking voor bepaalde periode
- Wachttijd voor uitkering
- Premiekosten afwegen tegen risico
- Combinatie met woonlastenverzekering mogelijk
""",

    "annuitair_dalende_orv": """
Een annuïtair dalende overlijdensrisicoverzekering is een vorm van levensverzekering waarbij het verzekerde bedrag gedurende de looptijd daalt.

Kenmerken:
- Verzekerd bedrag daalt eerst langzaam, later sneller
- Daling vaak gelijk aan hypotheekrente percentage
- Uitkering loopt gelijk met openstaande hypotheekschuld
- Lagere premie dan bij gelijkblijvende verzekering
- Medische acceptatie vereist
""",

    "lineair_dalende_orv": """
Een lineair dalende overlijdensrisicoverzekering is een vorm van levensverzekering waarbij het verzekerde bedrag in gelijke stappen daalt.

Kenmerken:
- Verzekerd bedrag daalt jaarlijks met gelijk bedrag
- Daling in rechte lijn tot nul
- Lagere premie dan bij gelijkblijvende verzekering
- Medische acceptatie vereist
- Vaste jaarlijkse afname verzekerd bedrag
""",

    "gelijkblijvende_orv": """
Een gelijkblijvende overlijdensrisicoverzekering houdt hetzelfde verzekerde bedrag gedurende de hele looptijd.

Kenmerken:
- Verzekerd bedrag blijft gelijk
- Premie blijft gelijk
- Uitkering onafhankelijk van moment overlijden
- Medische acceptatie vereist
- Hogere premie dan bij dalende verzekeringen
""",

    "nabestaandenpensioen": """
Het nabestaandenpensioen is een uitkering voor uw partner en/of kinderen na uw overlijden, meestal gekoppeld aan uw pensioenregeling.

Kenmerken:
- Standaard onderdeel pensioenregeling
- Uitkering voor partner
- Extra uitkering voor kinderen tot 21 jaar of studerend
- Aanvulling op andere voorzieningen mogelijk
- Belangrijk onderdeel financiële planning
""",

    "anw_hiaat": """
Een ANW-hiaatverzekering biedt extra financiële zekerheid voor uw nabestaanden, onafhankelijk van hun eigen inkomen.

Kenmerken:
- Vooraf vastgesteld uitkeringsbedrag
- Onafhankelijk van partnerinkomen
- Aanvulling op nabestaandenpensioen
- Extra financiële zekerheid
- Compensatie inkomensverlies na overlijden
"""
}

def improve_explanation(term: str, base_uitleg: str, originele_tekst: str, client) -> str:
    """Improves the explanation by naturally integrating definitions into the text."""
    try:
        if not client:
            return originele_tekst

        prompt = f"""Je bent een ervaren financieel adviseur die een hypotheekadvies verbetert. 
Integreer extra uitleg over {term} op een natuurlijke manier in de bestaande tekst.

EXTRA INFORMATIE OVER {term}:
{base_uitleg}

HUIDIGE TEKST:
{originele_tekst}

INSTRUCTIES:
1. Integreer de uitleg vloeiend in de bestaande tekst
2. Behoud ALLE informatie uit de huidige tekst
3. Verwijder alle kopjes zoals 'BASISUITLEG' of 'UITGEBREIDE UITLEG'
4. Maak de tekst een doorlopend geheel
5. Gebruik concrete voorbeelden uit de klantsituatie
6. Vermijd verwijzingen naar toekomstige gesprekken
7. Maak duidelijke verbanden tussen de uitleg en de specifieke situatie van de klant

Geef alleen de verbeterde, complete tekst terug zonder extra kopjes of secties."""

        response = client.chat.completions.create(
            model="gpt-4o-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        
        # Clean up any remaining headers or separators
        cleaned_result = result.replace("HUIDIGE TEKST MET TOEGEVOEGDE UITLEG:", "").strip()
        cleaned_result = cleaned_result.replace("BASISUITLEG:", "").strip()
        cleaned_result = cleaned_result.replace("UITGEBREIDE UITLEG:", "").strip()
        
        return cleaned_result if cleaned_result else originele_tekst

    except Exception as e:
        logging.error(f"Error improving explanation: {str(e)}")
        return originele_tekst 
