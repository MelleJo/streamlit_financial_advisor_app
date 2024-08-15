import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from streamlit_lottie import st_lottie
import requests

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    .main {
        background-color: #f8f9fa;
    }
    
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    h1, h2, h3 {
        color: #2c3e50;
    }
    
    .stButton>button {
        color: #ffffff;
        background-color: #3498db;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2980b9;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stTextInput>div>div>input {
        border-radius: 4px;
    }
    
    .stTextArea>div>div>textarea {
        border-radius: 4px;
    }
    
    .css-1aumxhk {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .result-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .result-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)

def render_home_screen():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("AI Hypotheek Assistent")
        st.write("Welkom bij de toekomst van hypotheekadvies. Onze AI-assistent staat klaar om uw notities te analyseren en waardevolle inzichten te bieden.")
        
        st.write("Hoe wilt u beginnen?")
        col3, col4, col5 = st.columns([1, 1, 1])
        with col3:
            if st.button("📝 Handmatige Invoer", use_container_width=True):
                switch_page("input")
        with col4:
            if st.button("📁 Bestand Uploaden", use_container_width=True):
                switch_page("upload")
    
    with col2:
        lottie_url = "https://assets1.lottiefiles.com/packages/lf20_V9t630.json"
        lottie_json = load_lottie_url(lottie_url)
        st_lottie(lottie_json, height=300)

def render_input_screen(gpt_service):
    st.title("Handmatige Invoer")
    st.write("Voer hier uw notities in en laat onze AI-assistent ze analyseren.")
    
    transcript = st.text_area("Voer het transcript in:", height=300)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔍 Analyseer", use_container_width=True):
            if transcript:
                with st.spinner("Bezig met analyseren..."):
                    result = gpt_service.analyze_transcript(transcript)
                st.session_state.result = result
                switch_page("results")
            else:
                st.error("Voer een transcript in om te analyseren.")

def render_upload_screen(gpt_service):
    st.title("Bestand Uploaden")
    st.write("Upload uw transcript bestand en laat onze AI-assistent het analyseren.")
    
    uploaded_file = st.file_uploader("Kies een bestand", type=["txt", "docx"])
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔍 Analyseer", use_container_width=True):
            if uploaded_file is not None:
                transcript = uploaded_file.read().decode("utf-8")
                with st.spinner("Bezig met analyseren..."):
                    result = gpt_service.analyze_transcript(transcript)
                st.session_state.result = result
                switch_page("results")
            else:
                st.error("Upload een geldig bestand om te analyseren.")

def render_result_screen():
    st.title("Analyse Resultaten")
    st.write("Hier zijn de inzichten die onze AI-assistent heeft gegenereerd op basis van uw input.")
    
    result = st.session_state.get("result", None)
    if result:
        for section, content in result.items():
            with st.expander(section.replace("_", " ").capitalize(), expanded=True):
                st.markdown(f'<div class="result-card">{content}</div>', unsafe_allow_html=True)
    else:
        st.warning("Er zijn geen resultaten beschikbaar.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 Terug naar Start", use_container_width=True):
            switch_page("home")

def render_footer():
    st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 14px; color: #666;">
    © 2024 AI Hypotheek Assistent | Een product van FutureFin Technologies
    </div>
    """, unsafe_allow_html=True)