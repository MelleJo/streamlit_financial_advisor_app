"""
File: templates.py
Contains section templates for all modules of the Veldhuis Advies Assistant.
"""

HYPOTHEEK_TEMPLATES = {
    "adviesmotivatie_leningdeel": """Op basis van de besproken situatie volgt een uitgebreide analyse van de hypothecaire financiering. Dit advies is toegespitst op de persoonlijke situatie en wensen, rekening houdend met zowel de korte als lange termijn perspectieven.

1. Situatiebeschrijving
De aankoop van een woning met een koopsom van {koopsom} wordt overwogen. Een hypotheek van {leenbedrag} wordt gewenst, waarbij {eigen_middelen} aan eigen middelen wordt ingebracht. Deze constructie valt binnen de verantwoorde leencapaciteit.

2. Gekozen Oplossing
Er is gekozen voor een {hypotheekvorm} met een looptijd van {looptijd} jaar en een rentevaste periode van {rentevaste_periode} jaar. De hypotheek wordt afgesloten met {nhg_status}. Deze opzet biedt een goede balans tussen zekerheid en flexibiliteit.

3. Conclusie en Overwegingen
De gekozen hypotheekconstructie sluit aan bij de financiële situatie en toekomstplannen. De lasten zijn binnen de verantwoorde normen en de gekozen rentevaste periode biedt langdurige zekerheid. Het gekozen aflossingsschema past bij het inkomensperspectief.""",

    "adviesmotivatie_werkloosheid": """Een grondige risicoanalyse is uitgevoerd met betrekking tot de financiële impact van mogelijke werkloosheid en de gewenste beschermingsmaatregelen.

1. Huidige Financiële Situatie
Het gezamenlijke netto inkomen bedraagt {inkomen} per maand. Hieruit worden de hypotheeklasten van {hypotheeklasten} voldaan. De overige vaste lasten zijn in kaart gebracht en laten voldoende ruimte voor reserveringen.

2. Risicoanalyse en Dekking
Bij werkloosheid kan een inkomensterugval ontstaan die impact heeft op het besteedbaar inkomen. Een werkloosheidsverzekering met een dekking van {dekking} per maand is overwogen om dit risico te beperken. Deze dekking vormt een aanvulling op eventuele wettelijke uitkeringen.

3. Beschermingsmaatregelen
De voorgestelde verzekering biedt financiële zekerheid en waarborgt de continuïteit van de hypotheekbetalingen. Deze bescherming sluit aan bij de wens voor financiële stabiliteit en de gekozen hypotheekconstructie.""",

    "adviesmotivatie_aow": """Een uitgebreide analyse is gemaakt van de financiële situatie rondom pensionering, waarbij gekeken is naar zowel de AOW als aanvullende pensioenvoorzieningen.

1. Pensioensituatie
De huidige pensioenopbouw via de werkgever(s) vormt de basis voor de financiële situatie na pensionering. De verwachte AOW-uitkering en het opgebouwde pensioen zijn in kaart gebracht.

2. Financiële Planning
De hypotheek wordt volgens schema afgelost, wat resulteert in lagere lasten bij pensionering. De gekozen hypotheekconstructie houdt rekening met de verwachte inkomensontwikkeling en het pensioenmoment.

3. Maatregelen en Voorzieningen
De hypotheekoplossing is afgestemd op de pensioensituatie. {pensioen_details} De financiële planning biedt ruimte voor aanvullende pensioenopbouw indien gewenst."""
}

PENSIOEN_TEMPLATES = {
    "samenvatting": """Een grondige analyse is gemaakt van de huidige en toekomstige pensioensituatie om een compleet beeld te krijgen van de financiële positie na pensionering.

1. Huidige Opbouw
De pensioenopbouw via de huidige werkgever biedt een basis van {pensioen_opbouw} bruto per jaar vanaf de pensioendatum. Dit wordt aangevuld met de AOW-uitkering van {aow_uitkering} per jaar.

2. Financiële Doelstellingen
Het gewenste besteedbaar inkomen na pensionering is vastgesteld op {gewenst_inkomen} netto per maand. Dit bedrag is gebaseerd op de huidige uitgavenpatronen en toekomstplannen.

3. Advies en Planning
De analyse toont een {verschil_tekst} tussen de verwachte en gewenste financiële situatie na pensionering. Het advies richt zich op het optimaliseren van de pensioenopbouw en het creëren van aanvullende voorzieningen."""
}

FP_TEMPLATES = {
    "samenvatting": """Een complete financiële planning is opgesteld om inzicht te geven in de huidige en toekomstige financiële situatie.

1. Financiële Uitgangspositie
Het gezamenlijke netto inkomen bedraagt {inkomen} per maand. De vaste lasten, inclusief hypotheek van {hypotheeklasten}, zijn in kaart gebracht. Er is een vrije financiële ruimte van {vrije_ruimte} per maand.

2. Toekomstscenario's
De planning houdt rekening met verschillende levensfases en scenario's, waaronder pensionering, arbeidsongeschiktheid en overlijden. Elk scenario is doorgerekend op financiële impact.

3. Adviezen en Aanbevelingen
Op basis van de analyse worden concrete stappen voorgesteld om de financiële doelen te realiseren. Deze omvatten vermogensopbouw, risicobeheer en fiscale optimalisatie."""
}
