"""
File: definitions.py
Contains mortgage-related definitions and explanation enhancement functionality for the AI Hypotheek Assistent.
This module provides:
1. A comprehensive dictionary of mortgage-related terms and their explanations in Dutch,
   covering key concepts like NHG, mortgage types, fixed interest periods, etc.
2. A function to improve explanations by integrating basic definitions into the original
   advice text in a natural and professional way using GPT-4.
"""

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
}

def improve_explanation(term, base_uitleg, originele_tekst, client):
    prompt = f"""Je bent een ervaren financieel adviseur die een collega helpt om een hypotheekadvies te verbeteren.

CONTEXT:
- De originele tekst van je collega bevat alle essentiële adviesinformatie
- Je moet deze informatie EXACT behouden
- Je taak is ALLEEN om een heldere uitleg over '{term}' toe te voegen
- Integreer de volgende basisuitleg op een natuurlijke manier:

BASISUITLEG:
{base_uitleg}

ORIGINELE TEKST VAN COLLEGA:
{originele_tekst}

INSTRUCTIES:
1. Behoud ALLE originele informatie en advies
2. Voeg de uitleg over {term} op een logische plek toe
3. Zorg voor vloeiende overgangen
4. Gebruik professionele maar begrijpelijke taal

Let op: Je mag het originele advies NIET wijzigen, alleen aanvullen met de uitleg."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Fout bij het genereren van de verbeterde tekst: {str(e)}"
