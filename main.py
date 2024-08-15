import streamlit as st
from gpt_service import GPTService
from audio_service import AudioService
from transcription_service import TranscriptionService
from ui_components import apply_custom_css, render_choose_method, render_upload, render_results

# Fetch the API key from Streamlit secrets
api_key = st.secrets["API"]["OPENAI_API_KEY"]

# Ensure the API key is provided
if not api_key:
    st.error("API key for GPT is missing. Please set it in Streamlit secrets.")
else:
    # Initialize services with the API key
    gpt_service = GPTService(api_key)
    audio_service = AudioService()
    transcription_service = TranscriptionService()

    # Apply custom CSS for improved UI
    apply_custom_css()

    # Initialize the session state if not already initialized
    if 'step' not in st.session_state:
        st.session_state.step = "choose_method"
    if 'upload_method' not in st.session_state:
        st.session_state.upload_method = None

    # Main logic to handle steps in the app
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
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
