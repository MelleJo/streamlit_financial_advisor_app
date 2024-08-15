import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        max-width: none;
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

    .section-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 1em;
        margin-bottom: 0.5em;
        background-color: #e2e8f0;
        padding: 0.5em;
        border-radius: 6px;
    }

    .result-title {
        font-weight: bold;
        margin-top: 0.5em;
    }

    .feedback-card {
        background-color: #f1f5f9;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .feedback-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 1em;
        color: #3b82f6;
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
            st.session_state.transcript = transcript
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
                st.markdown(f'<div class="section-title">{section.replace("_", " ").capitalize()}</div>', unsafe_allow_html=True)
                for line in content.split('\n'):
                    if line.strip().startswith('**') and line.strip().endswith('**'):
                        st.markdown(f'<div class="result-title">{line.strip()[2:-2]}</div>', unsafe_allow_html=True)
                    else:
                        st.write(line)
    else:
        st.warning("Er zijn geen resultaten beschikbaar.")
    
    render_feedback_section()

    if st.button("Terug naar Start", use_container_width=True):
        st.session_state.step = "choose_method"
        st.experimental_rerun()

def render_progress_bar():
    step = st.session_state.get("step", "choose_method")
    steps = ["choose_method", "upload", "results"]
    current_step = steps.index(step) + 1
    st.progress(current_step / len(steps))

def render_feedback_section():
    st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
    st.markdown('<div class="feedback-title">Feedback geven</div>', unsafe_allow_html=True)
    st.write("We waarderen uw feedback om onze service te verbeteren.")
    
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("Uw naam")
    with col2:
        feedback_type = st.selectbox("Type feedback", ["Positief", "Negatief"])
    
    feedback_text = st.text_area("Uw feedback")
    
    if st.button("Verstuur Feedback", key="submit_feedback"):
        if user_name and feedback_text:
            send_feedback_email(user_name, feedback_type, feedback_text)
        else:
            st.error("Vul alstublieft uw naam en feedback in.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def send_feedback_email(user_name, feedback_type, feedback_text):
    try:
        # Print all available secret keys (but not their values) for debugging
        st.write("Available secret keys:", list(st.secrets.keys()))

        # Check if email configuration exists in secrets
        if 'email' not in st.secrets:
            st.error("Email configuration is missing in secrets. Please check your secrets.toml file.")
            return

        # Access email configuration
        email_config = st.secrets['email']

        # Check if all required email configuration fields are present
        required_fields = ['username', 'password', 'smtp_server', 'smtp_port', 'receiving_email']
        missing_fields = [field for field in required_fields if field not in email_config]
        if missing_fields:
            st.error(f"Missing email configuration fields: {', '.join(missing_fields)}")
            return

        msg = MIMEMultipart()
        msg['From'] = email_config['username']
        msg['To'] = email_config['receiving_email']
        msg['Subject'] = f"AI Hypotheek Assistent Feedback - {feedback_type}"

        body = f"""
        Naam van gebruiker: {user_name}
        Type feedback: {feedback_type}
        Feedback: {feedback_text}

        Input (transcript):
        {st.session_state.get('transcript', 'Geen transcript beschikbaar')}

        Output:
        {st.session_state.get('result', 'Geen resultaten beschikbaar')}
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()
        server.login(email_config['username'], email_config['password'])
        text = msg.as_string()
        server.sendmail(email_config['username'], email_config['receiving_email'], text)
        server.quit()
        st.success("Feedback successfully sent!")
    except Exception as e:
        st.error(f"Er is een fout opgetreden bij het verzenden van de feedback: {str(e)}")