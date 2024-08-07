import streamlit as st
from audio_service import AudioService
from transcription_service import TranscriptionService
from gpt_service import GPTService
from ui_components import UIComponents

def load_openai_api_key():
    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key:
        st.error("OpenAI API key not found in Streamlit secrets. Please set the OPENAI_API_KEY in .streamlit/secrets.toml file.")
        st.stop()
    return api_key

def main():
    st.set_page_config(page_title="AI Hypotheek Assistent", layout="wide")
    st.title("AI Hypotheek Assistent")

    api_key = load_openai_api_key()

    audio_service = AudioService()
    transcription_service = TranscriptionService()
    gpt_service = GPTService(api_key)
    ui_components = UIComponents()

    # Input method selection
    input_method = st.radio("Kies een invoermethode:", ("Typen/Plakken", "Spreken", "Audio bestand uploaden"))

    transcript = None

    if input_method == "Typen/Plakken":
        # Stap 1: Tekst invoeren
        transcript = ui_components.text_input()
    elif input_method == "Spreken":
        # Stap 1: Audio opnemen
        audio_data = audio_service.record_audio()
        if audio_data:
            # Stap 2: Audio transcriberen
            transcript = transcription_service.transcribe(audio_data)
    elif input_method == "Audio bestand uploaden":
        # Stap 1: Audio bestand uploaden
        audio_file = ui_components.upload_audio()
        if audio_file:
            # Stap 2: Audio transcriberen
            transcript = transcription_service.transcribe(audio_file)

    if transcript:
        # Stap 3: Transcript analyseren met GPT
        adviesmodules = gpt_service.analyze_transcript(transcript)

        if adviesmodules is not None:
            # Stap 4: Resultaten weergeven en feedback krijgen
            final_adviesmodules = ui_components.display_and_refine_adviesmodules(adviesmodules, gpt_service)

            # Stap 5: Kopieerknopppen voor elk adviesmodule
            ui_components.add_copy_buttons(final_adviesmodules)
        else:
            st.error("Er is een fout opgetreden bij het analyseren van de transcript. Probeer het opnieuw of neem contact op met de ondersteuning.")

if __name__ == "__main__":
    main()