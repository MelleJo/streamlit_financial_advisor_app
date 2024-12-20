"""
File: transcription_service.py
Handles audio transcription functionality for the AI Hypotheek Assistent.
"""

import streamlit as st
from openai import OpenAI
from typing import Optional, Union, BinaryIO, Literal
import tempfile
import os
import logging
import ffmpeg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        try:
            # Try to get API key from secrets with better error handling
            api_key = st.secrets.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in secrets")
                
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.openai_client = None
            
        # Initialize Groq client if available
        try:
            groq_api_key = st.secrets.get("GROQ_API_KEY")
            if groq_api_key:
                from groq import Groq
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info("Groq client initialized successfully")
            else:
                self.groq_client = None
                
        except Exception as e:
            logger.info(f"Groq client not initialized: {str(e)}")
            self.groq_client = None

    def _convert_audio_to_mp3(self, audio_data: Union[bytes, BinaryIO]) -> bytes:
        """Convert audio to MP3 format using ffmpeg."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_input:
                if isinstance(audio_data, bytes):
                    temp_input.write(audio_data)
                else:
                    temp_input.write(audio_data.getvalue())
                temp_input.flush()

                # Create temporary output file
                temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_output.close()

                try:
                    # Convert to MP3
                    (
                        ffmpeg
                        .input(temp_input.name)
                        .output(temp_output.name, acodec='libmp3lame', ar='16000')
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True)
                    )

                    # Read the converted file
                    with open(temp_output.name, 'rb') as f:
                        return f.read()

                finally:
                    # Clean up temporary files
                    os.unlink(temp_input.name)
                    os.unlink(temp_output.name)

        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            raise Exception(f"Failed to convert audio: {str(e)}")

    def transcribe(
        self, 
        audio_input: Union[bytes, BinaryIO], 
        mode: Literal["fast", "accurate", "fallback"] = "accurate",
        language: str = "nl",
        prompt: Optional[str] = None
    ) -> Optional[str]:
        """Main transcription method that handles all transcription needs."""
        try:
            if not self.openai_client:
                st.error("OpenAI API key is required for transcription")
                return None

            # Convert audio to MP3 format
            logger.info("Converting audio to MP3 format...")
            try:
                audio_data = self._convert_audio_to_mp3(audio_input)
            except Exception as e:
                logger.error(f"Audio conversion failed: {str(e)}")
                st.error("Error converting audio. Please ensure the audio file is valid.")
                return None

            # Try Groq first if available and accurate mode is requested
            if mode == "accurate" and self.groq_client:
                try:
                    return self._transcribe_with_groq(audio_data, language, prompt)
                except Exception as e:
                    logger.warning(f"Groq transcription failed: {str(e)}. Falling back to Whisper.")
            
            # Otherwise use Whisper
            return self._transcribe_with_whisper(audio_data, language)
                
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            st.error("Er is een fout opgetreden tijdens de transcriptie. Probeer het opnieuw.")
            return None

    def _transcribe_with_groq(
        self, 
        audio_data: bytes,
        language: str = "nl",
        prompt: Optional[str] = None
    ) -> str:
        """Transcribes audio using Groq's Whisper Large V3 Turbo."""
        if not self.groq_client:
            raise Exception("Groq client not initialized")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            try:
                temp_audio_file.write(audio_data)
                temp_audio_file.flush()

                with open(temp_audio_file.name, "rb") as audio_file:
                    response = self.groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        language=language,
                        prompt=prompt,
                        response_format="text",
                        temperature=0.0
                    )
                
                logger.info("Successfully transcribed with Groq")
                return response.text

            finally:
                if os.path.exists(temp_audio_file.name):
                    os.unlink(temp_audio_file.name)

    def _transcribe_with_whisper(
        self, 
        audio_data: bytes,
        language: str = "nl"
    ) -> str:
        """Transcribes audio using OpenAI's Whisper."""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            try:
                temp_audio_file.write(audio_data)
                temp_audio_file.flush()

                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        with open(temp_audio_file.name, "rb") as audio_file:
                            response = self.openai_client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                language=language,
                                response_format="text"
                            )
                        
                        logger.info("Successfully transcribed with Whisper")
                        return response
                    
                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            raise e
                        logger.warning(f"Transcription attempt {retry_count} failed: {str(e)}")
                        continue

            finally:
                if os.path.exists(temp_audio_file.name):
                    os.unlink(temp_audio_file.name)