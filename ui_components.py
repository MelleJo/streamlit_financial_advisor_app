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

    def display_and_refine_adviesmodules(self, adviesmodules, gpt_service):
        st.subheader("Analyseresultaten")
        
        if adviesmodules is None or len(adviesmodules) == 0:
            st.warning("Er zijn geen adviesmodules om weer te geven. Probeer de analyse opnieuw uit te voeren.")
            return None

        final_adviesmodules = adviesmodules.copy()
        
        for module_name, content in adviesmodules.items():
            st.write(f"**{module_name}:**")
            new_content = st.text_area(f"Bewerk {module_name}", value=content, height=300, key=module_name)
            final_adviesmodules[module_name] = new_content

        feedback = st.text_area("Geef aanvullende feedback voor verfijning (optioneel)")
        
        if st.button("Verfijn Analyse"):
            transcript = "\n".join([f"<{module_name}>\n{content}\n</{module_name}>" for module_name, content in final_adviesmodules.items()])
            refined_adviesmodules = gpt_service.analyze_transcript(transcript)
            if refined_adviesmodules:
                final_adviesmodules = refined_adviesmodules
                st.success("Analyse verfijnd op basis van feedback!")
            else:
                st.error("Er is een fout opgetreden bij het verfijnen van de analyse. Probeer het opnieuw of neem contact op met de ondersteuning.")
            
        return final_adviesmodules

    def add_copy_buttons(self, adviesmodules):
        if adviesmodules is None or len(adviesmodules) == 0:
            return

        st.subheader("Kopieer Resultaten")
        
        for module_name, content in adviesmodules.items():
            if st.button(f"Kopieer {module_name}"):
                pyperclip.copy(content)
                st.success(f"{module_name} gekopieerd naar klembord!")

        if st.button("Kopieer Alle Adviesmodules"):
            all_content = "\n\n".join([f"{module_name}:\n{content}" for module_name, content in adviesmodules.items()])
            pyperclip.copy(all_content)
            st.success("Alle adviesmodules gekopieerd naar klembord!")