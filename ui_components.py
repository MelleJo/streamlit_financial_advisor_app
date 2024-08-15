import streamlit as st
from streamlit_mic_recorder import mic_recorder
from streamlit_extras.colored_header import colored_header

def apply_custom_css():
    st.markdown("""
        <style>
            .main {
                background-color: #f5f7fa;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .sidebar .sidebar-content {
                background-color: #ffffff;
                padding: 20px;
                box-shadow: 2px 0px 5px rgba(0, 0, 0, 0.1);
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
                border-radius: 8px;
                transition: background-color 0.3s;
            }
            .stButton > button:hover {
                background-color: #45a049;
            }
            .stTextInput > div > div > input {
                border-radius: 8px;
            }
            .stTextArea > div > div > textarea {
                border-radius: 8px;
            }
            .css-1aumxhk {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
        </style>
    """, unsafe_allow_html=True)

def render_home_screen():
    colored_header(label="Welkom bij de Hypotheek Assistent", description="Kies het type invoer dat u wilt gebruiken:", color_name="green-70")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Handmatige invoer", key="text_input_button", use_container_width=True):
            st.session_state.page = "text_input"
            st.experimental_rerun()
    
    with col2:
        if st.button("📁 Bestand uploaden", key="file_input_button", use_container_width=True):
            st.session_state.page = "file_input"
            st.experimental_rerun()

def render_text_input_screen(gpt_service):
    colored_header(label="Handmatige Invoer", description="Voer hier uw notities in", color_name="blue-70")
    transcript = st.text_area("Voer het transcript in:", key="text_input_area", height=300)
    
    if st.button("🔍 Analyseer Transcript", key="analyze_text_button"):
        if transcript:
            st.session_state.transcript = transcript
            with st.spinner("Bezig met analyseren... dit kan even duren."):
                st.session_state.result = gpt_service.analyze_transcript(transcript)
            st.session_state.page = "results"
            st.experimental_rerun()
        else:
            st.error("Voer een transcript in om te analyseren.")

def render_file_input_screen(gpt_service):
    colored_header(label="Bestand Uploaden", description="Upload uw transcript bestand", color_name="blue-70")
    uploaded_file = st.file_uploader("Upload uw transcript bestand", type=["txt", "docx"], key="file_input_uploader")
    
    if st.button("🔍 Analyseer Transcript", key="analyze_file_button"):
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
    colored_header(label="Analyse Resultaten", description="Hier zijn de resultaten van de analyse", color_name="green-70")
    result = st.session_state.get("result", None)
    if result:
        for section, content in result.items():
            with st.expander(section.replace("_", " ").capitalize(), expanded=True):
                st.markdown(content)
    else:
        st.write("Er zijn geen resultaten beschikbaar.")
    
    if st.button("🏠 Terug naar Start", key="back_to_home_button"):
        st.session_state.page = "home"
        st.experimental_rerun()

def render_footer():
    st.markdown("""
        <hr>
        <center style='color: #666; font-size: 14px;'>
            Gemaakt met ❤️ door AI Hypotheek Assistent Team
            <br>
            © 2024 AI Hypotheek Assistent
        </center>
        """, unsafe_allow_html=True)