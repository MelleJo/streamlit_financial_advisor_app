import streamlit as st
from gpt_service import GPTService
from audio_service import AudioService
from transcription_service import TranscriptionService
from ui_components import apply_custom_css, render_choose_method, render_upload, render_results

# Initialize services
gpt_service = GPTService()
audio_service = AudioService()
transcription_service = TranscriptionService()

# Apply custom CSS for improved UI
apply_custom_css()

# Main logic to handle steps in the app
if 'step' not in st.session_state:
    st.session_state.step = "choose_method"

if st.session_state.step == "choose_method":
    render_choose_method()
elif st.session_state.step == "upload":
    render_upload(gpt_service, audio_service, transcription_service)
elif st.session_state.step == "results":
    render_results()

# Handling rerun or errors in steps
if 'step' in st.session_state:
    if st.session_state.step == "error":
        st.error("Something went wrong. Please try again.")
        st.session_state.step = "choose_method"
        st.experimental_rerun()
