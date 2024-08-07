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

    # Stap 1: Audio opnemen
    audio_data = audio_service.record_audio()

    if audio_data:
        # Stap 2: Audio transcriberen
        transcript = transcription_service.transcribe(audio_data)

        # Stap 3: Transcript analyseren met GPT
        fields = gpt_service.analyze_transcript(transcript)

        # Stap 4: Resultaten weergeven en feedback krijgen
        final_fields = ui_components.display_and_refine_fields(fields, gpt_service)

        # Stap 5: Kopieerknopppen voor elk veld
        ui_components.add_copy_buttons(final_fields)

if __name__ == "__main__":
    main()