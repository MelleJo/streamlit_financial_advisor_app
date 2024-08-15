import streamlit as st
from openai import OpenAI
import tempfile
import os
import mimetypes

class TranscriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["API"]["OPENAI_API_KEY"])

    def transcribe(self, audio_input):
        st.subheader("Transcribing Audio")
        with st.spinner("Transcribing..."):
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_audio_file:
                    if isinstance(audio_input, bytes):
                        # If audio_input is bytes (from recorded audio)
                        temp_audio_file.write(audio_input)
                    else:
                        # If audio_input is an UploadedFile object
                        temp_audio_file.write(audio_input.getvalue())
                    temp_audio_file.flush()

                    # Debug information
                    st.write(f"File size: {os.path.getsize(temp_audio_file.name)} bytes")
                    st.write(f"File type: {mimetypes.guess_type(temp_audio_file.name)[0]}")

                    # Use the temporary file for transcription
                    with open(temp_audio_file.name, "rb") as audio_file:
                        response = self.client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_file
                        )

                # Remove the temporary file
                os.unlink(temp_audio_file.name)

                transcript = response.text
                st.success("Transcription complete!")
                st.write(transcript)
                return transcript
            except Exception as e:
                st.error(f"An error occurred during transcription: {str(e)}")
                return None