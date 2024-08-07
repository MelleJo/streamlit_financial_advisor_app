import streamlit as st
import pyperclip

class UIComponents:
    def text_input(self):
        st.subheader("Voer uw tekst in")
        text = st.text_area("Typ of plak uw tekst hier", height=300)
        if st.button("Analyseer Tekst"):
            if text.strip():
                return text
            else:
                st.warning("Voer alstublieft tekst in voordat u op Analyseer drukt.")
        return None

    def upload_audio(self):
        st.subheader("Upload audiobestand")
        audio_file = st.file_uploader("Kies een audiobestand", type=["wav", "mp3", "m4a"])
        if audio_file is not None:
            st.audio(audio_file)
            if st.button("Transcribeer en Analyseer"):
                return audio_file
        return None

    def display_and_refine_fields(self, fields, gpt_service):
        st.subheader("Analyseresultaten")
        
        if fields is None or len(fields) == 0:
            st.warning("Er zijn geen velden om weer te geven. Probeer de analyse opnieuw uit te voeren.")
            return None

        final_fields = fields.copy()
        
        for field_name, content in fields.items():
            st.write(f"**{field_name}:**")
            new_content = st.text_area(f"Bewerk {field_name}", value=content, height=150, key=field_name)
            final_fields[field_name] = new_content

        feedback = st.text_area("Geef aanvullende feedback voor verfijning (optioneel)")
        
        if st.button("Verfijn Analyse"):
            transcript = "\n".join(final_fields.values())
            refined_fields = gpt_service.analyze_transcript(transcript, feedback)
            if refined_fields:
                final_fields = refined_fields
                st.success("Analyse verfijnd op basis van feedback!")
            else:
                st.error("Er is een fout opgetreden bij het verfijnen van de analyse. Probeer het opnieuw of neem contact op met de ondersteuning.")
            
        return final_fields

    def add_copy_buttons(self, fields):
        if fields is None or len(fields) == 0:
            return

        st.subheader("Kopieer Resultaten")
        
        for field_name, content in fields.items():
            if st.button(f"Kopieer {field_name}"):
                pyperclip.copy(content)
                st.success(f"{field_name} gekopieerd naar klembord!")