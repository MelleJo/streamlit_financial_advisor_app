import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        .stApp {
            max-width: 800px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

def render_progress_bar(step):
    steps = ["choose_method", "upload", "results"]
    current_step = steps.index(step) + 1
    st.progress(current_step / len(steps))

def render_choose_method(app_state):
    st.title("AI Hypotheek Assistent")
    st.write("Kies hoe je je gegevens wilt invoeren:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Tekst invoeren"):
            app_state.set_step("upload")
            app_state.set_user_input("text")
    with col2:
        if st.button("Audio uploaden"):
            app_state.set_step("upload")
            app_state.set_user_input("audio")

def render_upload(app_state, services):
    st.title("Upload je gegevens")
    
    if app_state.user_input == "text":
        user_input = st.text_area("Voer je tekst in:", height=300)
        if st.button("Verwerk tekst"):
            with st.spinner("Bezig met verwerken..."):
                result = services['gpt_service'].process_text(user_input)
                app_state.set_processing_result(result)
                app_state.set_step("results")
    
    elif app_state.user_input == "audio":
        uploaded_file = st.file_uploader("Upload je audio bestand", type=['mp3', 'wav'])
        if uploaded_file is not None:
            if st.button("Verwerk audio"):
                with st.spinner("Bezig met verwerken..."):
                    audio_content = services['audio_service'].process_audio(uploaded_file)
                    transcription = services['transcription_service'].transcribe_audio(audio_content)
                    result = services['gpt_service'].process_text(transcription)
                    app_state.set_processing_result(result)
                    app_state.set_step("results")

def render_results(app_state):
    st.title("Resultaten")
    st.write(app_state.processing_result)
    
    if st.button("Opnieuw beginnen"):
        app_state.reset()