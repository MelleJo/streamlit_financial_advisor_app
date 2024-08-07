import streamlit as st
import openai

class TranscriptionService:
    def transcribe(self, audio_data):
        st.subheader("Transcribing Audio")
        with st.spinner("Transcribing..."):
            try:
                response = openai.Audio.transcribe("whisper-1", audio_data)
                transcript = response['text']
                st.success("Transcription complete!")
                st.write(transcript)
                return transcript
            except Exception as e:
                st.error(f"An error occurred during transcription: {str(e)}")
                return None