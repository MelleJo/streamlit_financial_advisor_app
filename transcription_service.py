"""
File: transcription_service.py
Handles audio transcription functionality for the AI Hypotheek Assistent.
This service provides audio transcription capabilities using both Groq and OpenAI's Whisper models.
It implements a fallback mechanism where if the primary transcription service (Groq) fails,
it automatically falls back to using OpenAI's Whisper. The service supports different transcription
modes (fast, accurate, fallback) and handles various audio input formats.
"""

import streamlit as st
from openai import OpenAI
from groq import Groq
import tempfile
import os
import logging
from typing import Optional, Union, BinaryIO, Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        self.groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    def transcribe(
        self, 
        audio_input: Union[bytes, BinaryIO], 
        mode: Literal["fast", "accurate", "fallback"] = "accurate",
        language: str = "nl",
        prompt: Optional[str] = None
    ) -> Optional[str]:
        """Main transcription method that handles all transcription needs."""
        try:
            if mode == "fast":
                return self._transcribe_with_whisper(audio_input)
            elif mode == "accurate":
                try:
                    return self._transcribe_with_groq(audio_input, language, prompt)
                except Exception as e:
                    logger.warning(f"Groq transcription failed: {str(e)}. Falling back to Whisper.")
                    return self._transcribe_with_whisper(audio_input)
            else:  # fallback
                return self._transcribe_with_whisper(audio_input)
                
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            st.error("Er is een fout opgetreden tijdens de transcriptie. Probeer het opnieuw.")
            return None

    def _transcribe_with_groq(
        self, 
        audio_input: Union[bytes, BinaryIO],
        language: str = "nl",
        prompt: Optional[str] = None
    ) -> str:
        """Transcribes audio using Groq's Whisper Large V3 Turbo."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_audio_file:
            try:
                if isinstance(audio_input, bytes):
                    temp_audio_file.write(audio_input)
                else:
                    temp_audio_file.write(audio_input.getvalue())
                temp_audio_file.flush()

                with open(temp_audio_file.name, "rb") as audio_file:
                    response = self.groq_client.audio.transcriptions.create(
                        file=(temp_audio_file.name, audio_file.read()),
                        model="whisper-large-v3-turbo",
                        language=language,
                        prompt=prompt,
                        response_format="json",
                        temperature=0.0
                    )
                
                logger.info("Successfully transcribed with Groq")
                return response.text

            finally:
                if os.path.exists(temp_audio_file.name):
                    os.unlink(temp_audio_file.name)

    def _transcribe_with_whisper(
        self, 
        audio_input: Union[bytes, BinaryIO],
        language: str = "nl"
    ) -> str:
        """Transcribes audio using OpenAI's Whisper."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_audio_file:
            try:
                if isinstance(audio_input, bytes):
                    temp_audio_file.write(audio_input)
                else:
                    temp_audio_file.write(audio_input.getvalue())
                temp_audio_file.flush()

                with open(temp_audio_file.name, "rb") as audio_file:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language
                    )
                
                logger.info("Successfully transcribed with Whisper")
                return response.text

            finally:
                if os.path.exists(temp_audio_file.name):
                    os.unlink(temp_audio_file.name)
