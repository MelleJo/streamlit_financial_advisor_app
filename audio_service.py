import streamlit as st
from streamlit_mic_recorder import mic_recorder

class AudioService:
    def record_audio(self):
        st.subheader("Record Your Advisory Notes")
        st.write("Click the microphone button to start recording. Click again to stop.")

        audio = mic_recorder(start_prompt="Start Recording", stop_prompt="Stop Recording", key="recorder")

        if audio:
            st.audio(audio['bytes'])
            st.success("Audio recorded successfully!")
            return audio['bytes']
        
        return None