import streamlit as st
from streamlit_mic_recorder import mic_recorder

class AudioService:
    def record_audio(self):
        st.subheader("Neem uw adviesnotities op")
        st.write("Klik op de microfoonknop om de opname te starten. Klik nogmaals om te stoppen.")

        audio = mic_recorder(start_prompt="Start Opname", stop_prompt="Stop Opname", key="recorder")

        if audio:
            st.audio(audio['bytes'])
            st.success("Audio succesvol opgenomen!")
            return audio['bytes']
        
        return None