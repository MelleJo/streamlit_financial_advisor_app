import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
            .main {
                background-color: #f0f0f5;
                padding: 20px;
            }
            .sidebar .sidebar-content {
                background-color: #ffffff;
                padding: 20px;
            }
            .stButton > button {
                color: white;
                background-color: #4CAF50;
                border: none;
                padding: 10px 24px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 16px;
            }
        </style>
    """, unsafe_allow_html=True)

def render_home_screen():
    st.title("Welkom bij de Hypotheek Assistent")
    st.write("Kies het type invoer dat u wilt gebruiken:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Handmatige invoer"):
            st.session_state.page = "text_input"
    with col2:
        if st.button("Bestand uploaden"):
            st.session_state.page = "file_input"

def render_text_input_screen(gpt_service):
    st.header("Handmatige Invoer")
    transcript = st.text_area("Voer het transcript in:")
    
    if st.button("Analyseer Transcript"):
        if transcript:
            st.session_state.transcript = transcript
            with st.spinner("Bezig met analyseren... dit kan even duren."):
                st.session_state.result = gpt_service.analyze_transcript(transcript)
            st.session_state.page = "results"
            st.experimental_rerun()
        else:
            st.error("Voer een transcript in om te analyseren.")

def render_file_input_screen(gpt_service):
    st.header("Bestand Uploaden")
    uploaded_file = st.file_uploader("Upload uw transcript bestand", type=["txt", "docx"])
    
    if st.button("Analyseer Transcript") and uploaded_file:
        if uploaded_file is not None:
            transcript = uploaded_file.read().decode("utf-8")
            st.session_state.transcript = transcript
            with st.spinner("Bezig met analyseren... dit kan even duren."):
                st.session_state.result = gpt_service.analyze_transcript(transcript)
            st.session_state.page = "results"
            st.experimental_rerun()
        else:
            st.error("Upload een geldig bestand om te analyseren.")

def render_result_screen():
    st.header("Analyse Resultaten")
    result = st.session_state.get("result", None)
    if result:
        for section, content in result.items():
            st.subheader(section.replace("_", " ").capitalize())
            st.markdown(content)
    else:
        st.write("Er zijn geen resultaten beschikbaar.")
    
    if st.button("Terug naar Start"):
        st.session_state.page = "home"
        st.experimental_rerun()

def render_footer():
    st.markdown("""
        <hr>
        <center>Gemaakt met ❤️ door [Uw Naam]</center>
        """, unsafe_allow_html=True)
