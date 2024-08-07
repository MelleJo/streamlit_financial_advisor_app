import streamlit as st
import openai
import tempfile
import os

class TranscriptionService:
    def transcribe(self, audio_data):
        st.subheader("Transcribing Audio")
        with st.spinner("Transcribing..."):
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                    temp_audio_file.write(audio_data)
                    temp_audio_file.flush()

                    # Use the temporary file for transcription
                    with open(temp_audio_file.name, "rb") as audio_file:
                        response = openai.Audio.transcribe("whisper-1", audio_file)

                # Remove the temporary file
                os.unlink(temp_audio_file.name)

                transcript = response['text']
                st.success("Transcription complete!")
                st.write(transcript)
                return transcript
            except Exception as e:
                st.error(f"An error occurred during transcription: {str(e)}")
                return None