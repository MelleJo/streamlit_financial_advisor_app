import streamlit as st

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
        max-width: 800px;
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
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 6px;
    }
    
    .result-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

def render_choose_method():
    st.title("AI Hypotheek Assistent")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Handmatige Invoer", use_container_width=True, key="choose_manual_input"):
            st.session_state.upload_method = "manual"
            st.session_state.step = "upload"
            st.experimental_rerun()
    with col2:
        if st.button("📁 Bestand Uploaden", use_container_width=True, key="choose_file_upload"):
            st.session_state.upload_method = "file"
            st.session_state.step = "upload"
            st.experimental_rerun()

def render_upload(gpt_service):
    st.title("Transcript Invoer")
    if st.session_state.upload_method == "manual":
        transcript = st.text_area("Voer het transcript in:", height=300)
    else:
        uploaded_file = st.file_uploader("Kies een bestand", type=["txt", "docx"])
        transcript = uploaded_file.read().decode("utf-8") if uploaded_file else None
    
    if st.button("Analyseer", use_container_width=True):
        if transcript:
            with st.spinner("Bezig met analyseren..."):
                result = gpt_service.analyze_transcript(transcript)
            st.session_state.result = result
            st.session_state.step = "results"
            st.experimental_rerun()
        else:
            st.error("Voer een transcript in of upload een bestand om te analyseren.")

def render_results():
    st.title("Analyse Resultaten")
    
    result = st.session_state.get("result", None)
    if result:
        for section, content in result.items():
            with st.expander(section.replace("_", " ").capitalize(), expanded=True):
                st.markdown(f'<div class="result-card">{content}</div>', unsafe_allow_html=True)
    else:
        st.warning("Er zijn geen resultaten beschikbaar.")
    
    if st.button("Terug naar Start", use_container_width=True):
        st.session_state.step = "choose_method"
        st.experimental_rerun()

def render_progress_bar():
    step = st.session_state.get("step", "choose_method")
    steps = ["choose_method", "upload", "results"]
    current_step = steps.index(step) + 1
    st.progress(current_step / len(steps))