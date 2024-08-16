import streamlit as st
from streamlit_mic_recorder import mic_recorder

class AudioService:
    def __init__(self):
        self.audio_recorder = None

    def start_recording(self):
        st.subheader("Neem uw adviesnotities op")
        st.write("Klik op de 'Stop Opname' knop om de opname te stoppen.")
        self.audio_recorder = mic_recorder(start_prompt="", stop_prompt="", key="recorder")
        return self.audio_recorder

    def stop_recording(self, audio_recorder):
        if audio_recorder:
            audio = audio_recorder
            if audio:
                st.audio(audio['bytes'])
                st.success("Audio succesvol opgenomen!")
                return audio['bytes']
        return None