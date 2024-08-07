import streamlit as st
from audio_service import AudioService
from transcription_service import TranscriptionService
from gpt_service import GPTService
from ui_components import UIComponents

def main():
    st.set_page_config(page_title="Financial Advisor Assistant", layout="wide")
    st.title("Financial Advisor Assistant")

    audio_service = AudioService()
    transcription_service = TranscriptionService()
    gpt_service = GPTService()
    ui_components = UIComponents()

    # Step 1: Record audio
    audio_data = audio_service.record_audio()

    if audio_data:
        # Step 2: Transcribe audio
        transcript = transcription_service.transcribe(audio_data)

        # Step 3: Analyze transcript with GPT
        fields = gpt_service.analyze_transcript(transcript)

        # Step 4: Display results and get feedback
        final_fields = ui_components.display_and_refine_fields(fields, gpt_service)

        # Step 5: Copy buttons for each field
        ui_components.add_copy_buttons(final_fields)

if __name__ == "__main__":
    main()