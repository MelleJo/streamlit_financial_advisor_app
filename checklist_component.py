import streamlit as st

def display_checklist():
    st.subheader("Checklist voor opname")
    
    with st.expander("Klik hier om de checklist te bekijken"):
        st.markdown("""
        ### Adviesmotivatie leningdeel:
        - [ ] Leningbedrag en dekking (NHG)
        - [ ] Aflosvorm en looptijd
        - [ ] Rentevaste periode en motivatie
        - [ ] Fiscaal aspect (hypotheekrenteaftrek)
        - [ ] Voorkeuren van de klant
        - [ ] Aanvullende aanbevelingen

        ### Adviesmotivatie werkloosheid:
        - [ ] Doelstelling bij werkloosheid
        - [ ] Toetslast en verantwoorde maandlasten
        - [ ] Maximaal te verzekeren bedrag
        - [ ] Reactie van de klant op het advies

        ### Adviesmotivatie AOW:
        - [ ] Doelstelling vanaf AOW-datum
        - [ ] Status van hypotheekaflossing op AOW-datum
        - [ ] Financiële voordelen na AOW
        - [ ] Toekomstperspectief na pensionering
        - [ ] Aanvullende aanbevelingen voor na pensionering
        """)
        
        st.info("Gebruik deze checklist als herinnering voor wat u moet bespreken en opnemen in uw advies. Vink de items af naarmate u ze behandelt.")