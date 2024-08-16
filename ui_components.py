import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from docx import Document
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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

def render_progress_bar(app_state):
    steps = ["choose_method", "upload", "results"]
    current_step = steps.index(app_state.step) + 1
    st.progress(current_step / len(steps))

def render_choose_method(app_state):
    st.title("AI Hypotheek Assistent")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Handmatige Invoer", use_container_width=True):
            app_state.set_upload_method("manual")
            app_state.set_step("upload")
    with col2:
        if st.button("📁 Bestand Uploaden", use_container_width=True):
            app_state.set_upload_method("file")
            app_state.set_step("upload")
    with col3:
        if st.button("🎙️ Audio Opnemen", use_container_width=True):
            app_state.set_upload_method("audio")
            app_state.set_step("upload")

def render_upload(app_state, services):
    st.title("Transcript Invoer")
    transcript = None

    if app_state.upload_method == "manual":
        transcript = st.text_area("Voer het transcript in:", height=300)
        if st.button("Analyseer", use_container_width=True):
            process_transcript(transcript, services['gpt_service'], app_state)

    elif app_state.upload_method == "file":
        uploaded_file = st.file_uploader("Kies een bestand", type=["txt", "docx", "wav", "mp3", "m4a"])
        if uploaded_file:
            logger.info(f"Uploaded file: {uploaded_file.name}, Type: {uploaded_file.type}, Size: {uploaded_file.size} bytes")
            
            with st.spinner("Bestand wordt verwerkt..."):
                if uploaded_file.type.startswith('audio') or uploaded_file.name.lower().endswith(('.wav', '.mp3', '.m4a')):
                    transcript = services['transcription_service'].transcribe(uploaded_file)
                else:
                    transcript = uploaded_file.getvalue().decode("utf-8")
            
            if transcript:
                st.text_area("Transcript (bewerk indien nodig):", value=transcript, height=300, key="editable_transcript")
                if st.button("Analyseer", use_container_width=True):
                    process_transcript(st.session_state.editable_transcript, services['gpt_service'], app_state)
            else:
                st.error("Er is een fout opgetreden bij het verwerken van het bestand.")

    else:  # audio recording
        if st.button("Start Opname"):
            with st.spinner("Audio wordt opgenomen..."):
                audio_bytes = services['audio_service'].record_audio()
            
            if audio_bytes:
                with st.spinner("Audio wordt getranscribeerd..."):
                    transcript = services['transcription_service'].transcribe(audio_bytes)
                
                if transcript:
                    st.text_area("Transcript (bewerk indien nodig):", value=transcript, height=300, key="editable_transcript")
                    if st.button("Analyseer", use_container_width=True):
                        process_transcript(st.session_state.editable_transcript, services['gpt_service'], app_state)
                else:
                    st.error("Er is een fout opgetreden bij het transcriberen van de audio.")

def process_transcript(transcript, gpt_service, app_state):
    if transcript:
        with st.spinner("Bezig met analyseren..."):
            logger.info("Starting transcript analysis")
            result = gpt_service.analyze_transcript(transcript)
            logger.info("Transcript analysis completed")
        if result:
            app_state.set_result(result)
            app_state.set_transcript(transcript)
            app_state.set_step("results")
        else:
            logger.error("Error occurred during transcript analysis")
            st.error("Er is een fout opgetreden bij het analyseren van het transcript.")
    else:
        logger.warning("No transcript to analyze")
        st.error("Er is geen transcript om te analyseren. Voer een transcript in, upload een bestand, of neem audio op.")

def render_results(app_state):
    st.title("Analyse Resultaten")
    
    result = app_state.result
    if result:
        for section, content in result.items():
            with st.expander(section.replace("_", " ").capitalize(), expanded=True):
                st.markdown(f'<div class="section-title">{section.replace("_", " ").capitalize()}</div>', unsafe_allow_html=True)
                for line in content.split('\n'):
                    if line.strip().startswith('**') and line.strip().endswith('**'):
                        st.markdown(f'<div class="result-title">{line.strip()[2:-2]}</div>', unsafe_allow_html=True)
                    else:
                        st.write(line)
        
        if st.button("Exporteer als Word-document", use_container_width=True):
            export_to_docx(result)
    else:
        st.warning("Er zijn geen resultaten beschikbaar.")
    
    render_feedback_section(app_state)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Terug naar Start", use_container_width=True):
            app_state.set_step("choose_method")
    with col2:
        if st.button("Nieuwe Analyse", use_container_width=True):
            app_state.reset()

def render_feedback_section(app_state):
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
            send_feedback_email(user_name, feedback_type, feedback_text, app_state)
        else:
            st.error("Vul alstublieft uw naam en feedback in.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def send_feedback_email(user_name, feedback_type, feedback_text, app_state):
    try:
        if 'email' not in st.secrets:
            st.error("Email configuration is missing in secrets. Please check your secrets.toml file.")
            return

        email_config = st.secrets.email

        required_fields = ['username', 'password', 'smtp_server', 'smtp_port', 'receiving_email']
        missing_fields = [field for field in required_fields if not hasattr(email_config, field)]
        if missing_fields:
            st.error(f"Missing email configuration fields: {', '.join(missing_fields)}.")
            return

        msg = MIMEMultipart()
        msg['From'] = email_config.username
        msg['To'] = email_config.receiving_email
        msg['Subject'] = f"AI Hypotheek Assistent Feedback - {feedback_type}"

        body = f"""
        Naam van gebruiker: {user_name}
        Type feedback: {feedback_type}
        Feedback: {feedback_text}

        Input (transcript):
        {app_state.transcript}

        Output:
        {app_state.result}
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)
        server.starttls()
        server.login(email_config.username, email_config.password)
        text = msg.as_string()
        server.sendmail(email_config.username, email_config.receiving_email, text)
        server.quit()
        st.success("Feedback successfully sent!")
    except Exception as e:
        st.error(f"Er is een fout opgetreden bij het verzenden van de feedback: {str(e)}")

def export_to_docx(result):
    doc = Document()
    doc.add_heading('Analyse Resultaten', 0)

    for section, content in result.items():
        doc.add_heading(section.replace("_", " ").capitalize(), level=1)
        for line in content.split('\n'):
            if line.strip().startswith('**') and line.strip().endswith('**'):
                doc.add_paragraph(line.strip()[2:-2], style='Heading 2')
            else:
                doc.add_paragraph(line)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    
    st.download_button(
        label="Download Word Document",
        data=bio.getvalue(),
        file_name="analyse_resultaten.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )