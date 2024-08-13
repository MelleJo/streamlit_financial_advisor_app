import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

api_key = st.secrets["OPENAI_API_KEY"]

class GPTService:
    def __init__(self, api_key):
        # Use the ChatOpenAI initialization with the API key
        self.llm = ChatOpenAI(model_name="gpt-4o-2024-08-06", temperature=0.3, openai_api_key=api_key)
        self.prompt = PromptTemplate(
            input_variables=["transcript"],
            template="""
            Je bent een financieel adviseur die gespecialiseerd is in het analyseren van klantgesprekken en het opstellen van gedetailleerde adviesmodules. Je taak is om een transcript van een klantgesprek te analyseren en drie gestructureerde adviesmodules op te stellen: "Adviesmotivatie leningdeel", "Adviesmotivatie werkloosheid", en "Adviesmotivatie AOW". Volg de onderstaande richtlijnen zorgvuldig om elk adviesonderdeel volledig en gedetailleerd uit te werken.

            Hier is het transcript van het klantgesprek:

            <transcript>
            {transcript}
            </transcript>

            Analyseer het bovenstaande transcript zorgvuldig en let op alle details die relevant zijn voor de drie adviesmodules. Gebruik alleen informatie die expliciet in het transcript staat of die logisch kan worden afgeleid uit de gegeven informatie.

            Stel vervolgens de volgende drie adviesmodules op:

            1. Adviesmotivatie leningdeel:

            a) Leningbedrag en Dekking:
               - Noteer het exacte leningbedrag.
               - Vermeld of de lening is gedekt door een garantie zoals de Nationale Hypotheek Garantie (NHG).

            b) Aflosvorm en Looptijd:
               - Beschrijf de aflosvorm van de hypotheek (bijvoorbeeld annuïteitenhypotheek).
               - Vermeld de totale looptijd van de hypotheek in jaren.

            c) Rentevaste Periode:
               - Adviseer een specifieke duur voor de rentevaste periode.
               - Geef duidelijke redenen voor de keuze van deze rentevaste periode, gebaseerd op de wensen van de klant en de huidige renteomgeving.

            d) Fiscaal Aspect:
               - Leg uit of de hypotheekrente fiscaal aftrekbaar is en welke voordelen dit biedt.

            e) Voorkeur van de Klant:
               - Noteer eventuele specifieke voorkeuren van de klant, zoals lagere maandlasten in het begin of een voorkeur voor een bepaalde aflosvorm.

            f) Aanvullende Aanbevelingen:
               - Geef eventuele extra aanbevelingen, zoals het vastzetten van de rente voor een langere periode of het overwegen van toekomstige rentestijgingen.

            2. Adviesmotivatie werkloosheid:

            a) Doelstelling:
               - Beschrijf het doel van de klant om tijdens een periode van werkloosheid tegen verantwoorde maandlasten in de woning te kunnen blijven wonen.

            b) Kosten en Verantwoording:
               - Bereken de toetslast bij werkloosheid en vermeld dit bedrag.
               - Geef aan wat op dat moment als verantwoordelijke maandlasten wordt beschouwd.

            c) Verzekeringsadvies:
               - Adviseer welk bedrag maximaal te verzekeren is bij werkloosheid.
               - Bespreek eventuele beperkingen of onverzekerde bedragen.

            d) Reactie van de Klant:
               - Noteer de reactie van de klant op dit advies, bijvoorbeeld of ze het advies opvolgen of een andere aanpak kiezen.

            3. Adviesmotivatie AOW:

            a) Doelstelling:
               - Beschrijf het doel van de klant vanaf de AOW-datum om tegen verantwoorde maandlasten in de woning te blijven wonen.

            b) Aflossing:
               - Geef aan of de hypotheek volledig is afgelost op de AOW-datum.

            c) Financiële Voordelen:
               - Vermeld specifieke financiële voordelen of veranderingen die optreden na het bereiken van de AOW-leeftijd, zoals geen hypotheeklasten meer.

            d) Toekomstperspectief:
               - Beschrijf hoe de financiële situatie van de klant er na de AOW-leeftijd uit zal zien, rekening houdend met pensioeninkomsten en eventuele resterende hypotheeklasten.

            e) Aanvullende Aanbevelingen:
               - Geef eventuele extra aanbevelingen voor de periode na pensionering, zoals het opbouwen van extra reserves of het overwegen van aanvullende pensioenvoorzieningen.

            Presenteer je analyse en advies in de volgende structuur:

            <adviesmotivatie_leningdeel>
            [Vul hier de gedetailleerde adviesmotivatie voor het leningdeel in, volgens de bovenstaande richtlijnen]
            </adviesmotivatie_leningdeel>

            <adviesmotivatie_werkloosheid>
            [Vul hier de gedetailleerde adviesmotivatie voor werkloosheid in, volgens de bovenstaande richtlijnen]
            </adviesmotivatie_werkloosheid>

            <adviesmotivatie_aow>
            [Vul hier de gedetailleerde adviesmotivatie voor AOW in, volgens de bovenstaande richtlijnen]
            </adviesmotivatie_aow>

            Zorg ervoor dat je advies duidelijk, gedetailleerd en goed onderbouwd is, gebaseerd op de informatie uit het transcript. Als er cruciale informatie ontbreekt, geef dan aan dat er meer informatie nodig is om een volledig advies te kunnen geven.
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def analyze_transcript(self, transcript):
        st.subheader("Analyzing Transcript")
        with st.spinner("Analyzing..."):
            try:
                result = self.chain.run(transcript=transcript)
                st.success("Analysis complete!")
                return self._parse_result(result)
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                return None

    def _parse_result(self, result):
        # Parse the result into three separate sections
        sections = {
            "adviesmotivatie_leningdeel": "",
            "adviesmotivatie_werkloosheid": "",
            "adviesmotivatie_aow": ""
        }
        
        current_section = None
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('<adviesmotivatie_'):
                current_section = line[1:-1]  # Extract tag name without <>
            elif line.startswith('</adviesmotivatie_'):
                current_section = None
            elif current_section:
                sections[current_section] += line + '\n'
        
        # Remove any leading/trailing whitespace from each section
        sections = {key: value.strip() for key, value in sections.items()}
        
        return sections
