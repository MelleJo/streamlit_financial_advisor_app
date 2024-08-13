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

def render_sidebar():
    st.sidebar.title("Hypotheek Assistent")
    st.sidebar.write("Gebruik deze app om financiële adviezen te genereren op basis van transcripties.")
    st.sidebar.write("Kies een sectie om te beginnen:")

def render_tabs(gpt_service):
    tab1, tab2, tab3 = st.tabs(["📄 Analyseer Transcript", "📊 Resultaten", "⚙️ Instellingen"])

    with tab1:
        st.header("📄 Analyseer een Transcript")
        st.write("Upload hier een transcript om het te analyseren en gedetailleerde adviesmodules te genereren.")

        transcript = st.text_area("Voer het transcript in:")
        if st.button("Analyseer Transcript"):
            if transcript:
                result = gpt_service.analyze_transcript(transcript)
                st.session_state['result'] = result
            else:
                st.error("Voer een transcript in om te analyseren.")

    with tab2:
        st.header("📊 Analyse Resultaten")
        st.write("Hier worden de resultaten van de analyse weergegeven.")

        if 'result' in st.session_state:
            result = st.session_state['result']
            if result:
                for section, content in result.items():
                    with st.expander(section.replace("_", " ").capitalize()):
                        st.markdown(content)
            else:
                st.write("Er zijn nog geen resultaten beschikbaar. Ga naar de tab 'Analyseer Transcript' om te beginnen.")
        else:
            st.write("Er zijn nog geen resultaten beschikbaar. Ga naar de tab 'Analyseer Transcript' om te beginnen.")

    with tab3:
        st.header("⚙️ Instellingen")
        st.write("Configureer hier de instellingen van de app.")
        st.selectbox("Kies een model", ["GPT-3.5", "GPT-4"])
        st.slider("Kies de temperatuurinstelling voor het model:", 0.0, 1.0, 0.7)

def render_footer():
    st.markdown("""
        <hr>
        <center>Gemaakt met ❤️ door [Uw Naam]</center>
        """, unsafe_allow_html=True)
