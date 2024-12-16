import streamlit as st
from streamlit_mic_recorder import mic_recorder
from checklist_component import display_checklist

class AudioService:
    def record_audio(self):
        st.title("Financieel Advies Opname")

        # Display the checklist
        display_checklist()

        st.subheader("Neem uw adviesnotities op")
        st.write("Klik op de microfoonknop om de opname te starten. Klik nogmaals om te stoppen.")

        audio = mic_recorder(
            start_prompt="Start Opname",
            stop_prompt="Stop Opname",
            key="recorder"
        )

        if audio and audio.get('bytes'):
            # Add a preview of the recording
            st.audio(audio['bytes'])
            
            # Show success message with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ Audio succesvol opgenomen om {timestamp}")
            
            # Log the audio length for debugging
            import sys
            audio_size = sys.getsizeof(audio['bytes'])
            logger.info(f"Recorded audio size: {audio_size} bytes")
            
            return audio['bytes']
        
        return None