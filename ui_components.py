import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.colored_header import colored_header
import streamlit.components.v1 as components

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #f8fafc;
    }
    
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    h1 {
        color: #1e293b;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 600;
    }
    
    .stButton>button {
        color: #ffffff;
        background-color: #3b82f6;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
    }
    
    .stTextInput>div>div>input {
        border-radius: 6px;
    }
    
    .stTextArea>div>div>textarea {
        border-radius: 6px;
    }
    
    .css-1aumxhk {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .result-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .result-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stExpander {
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-radius: 10px;
    }
    
    .stExpander > div:first-child {
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }
    
    .stExpander > div:last-child {
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def render_navigation():
    selected = option_menu(
        menu_title=None,
        options=["Home", "Handmatige Invoer", "Bestand Uploaden", "Resultaten"],
        icons=["house", "pencil-square", "file-earmark-text", "graph-up"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f8fafc"},
            "icon": {"color": "#3b82f6", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#eef2ff"},
            "nav-link-selected": {"background-color": "#3b82f6", "color": "white"},
        }
    )
    return selected

def render_home_screen():
    colored_header(
        label="AI Hypotheek Assistent",
        description="Welkom bij de toekomst van hypotheekadvies",
        color_name="blue-70"
    )
    st.write("Onze AI-assistent staat klaar om uw notities te analyseren en waardevolle inzichten te bieden. Kies een optie om te beginnen.")

    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 Handmatige Invoer", use_container_width=True, key="home_manual_input")
    with col2:
        st.button("📁 Bestand Uploaden", use_container_width=True, key="home_file_upload")

def render_input_screen(gpt_service):
    colored_header(
        label="Handmatige Invoer",
        description="Voer hier uw notities in en laat onze AI-assistent ze analyseren",
        color_name="blue-70"
    )
    
    transcript = st.text_area("Voer het transcript in:", height=300)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔍 Analyseer", use_container_width=True):
            if transcript:
                with st.spinner("Bezig met analyseren..."):
                    result = gpt_service.analyze_transcript(transcript)
                st.session_state.result = result
                st.session_state.page = "results"
                st.experimental_rerun()
            else:
                st.error("Voer een transcript in om te analyseren.")

def render_upload_screen(gpt_service):
    colored_header(
        label="Bestand Uploaden",
        description="Upload uw transcript bestand en laat onze AI-assistent het analyseren",
        color_name="blue-70"
    )
    
    uploaded_file = st.file_uploader("Kies een bestand", type=["txt", "docx"])
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔍 Analyseer", use_container_width=True):
            if uploaded_file is not None:
                transcript = uploaded_file.read().decode("utf-8")
                with st.spinner("Bezig met analyseren..."):
                    result = gpt_service.analyze_transcript(transcript)
                st.session_state.result = result
                st.session_state.page = "results"
                st.experimental_rerun()
            else:
                st.error("Upload een geldig bestand om te analyseren.")

def render_result_screen():
    colored_header(
        label="Analyse Resultaten",
        description="Hier zijn de inzichten die onze AI-assistent heeft gegenereerd",
        color_name="blue-70"
    )
    
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
            st.session_state.page = "home"
            st.experimental_rerun()

def render_footer():
    st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #f8fafc; padding: 10px; text-align: center; font-size: 14px; color: #64748b; border-top: 1px solid #e2e8f0;">
    © 2024 AI Hypotheek Assistent | Een product van FutureFin Technologies
    </div>
    """, unsafe_allow_html=True)