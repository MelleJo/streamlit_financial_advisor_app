import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import docx

import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1f2937;
        height: 100%;
        width: 100%;
    }

    .main {
        background: linear-gradient(135deg, #e2e8f0, #f8fafc);
        padding: 2rem;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .stApp {
        width: 100%;
        max-width: 1100px;
        padding-top: 2rem;
        background-color: #ffffff;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border-radius: 12px;
        padding: 2rem;
        margin: 0 auto;
    }

    h1 {
        color: #111827;
        font-weight: 800;
        text-align: center;
        margin-bottom: 1.5rem;
        font-size: 2.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    p {
        text-align: center;
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }

    h2, h3 {
        color: #374151;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .stButton>button {
        color: #ffffff !important;
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        border: none;
        border-radius: 12px;
        padding: 0.85rem 1.7rem;
        font-weight: 600;
        font-size: 1.2rem;
        transition: all 0.3s ease;
        width: 100%;
        max-width: 300px;
        margin: 0 auto;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
        display: block;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.5);
        transform: translateY(-3px);
    }

    .stButton>button:active {
        background: linear-gradient(135deg, #1e40af, #1e3a8a);
        box-shadow: 0 6px 15px rgba(30, 64, 175, 0.4);
        transform: translateY(0);
    }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 0.7rem;
        font-size: 1rem;
        color: #374151;
        background-color: #f9fafb;
    }

    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.4);
    }

    .section-title {
        font-size: 1.4em;
        font-weight: bold;
        margin-top: 1.2em;
        margin-bottom: 0.6em;
        background-color: #e5e7eb;
        padding: 0.9rem;
        border-radius: 10px;
        color: #111827;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .result-title {
        font-weight: bold;
        margin-top: 0.6em;
        color: #111827;
    }

    .feedback-card {
        background-color: #f9fafb;
        border-radius: 12px;
        padding: 2.5rem;
        margin-top: 2.5rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
    }

    .feedback-title {
        font-size: 1.4em;
        font-weight: bold;
        margin-bottom: 1.8em;
        color: #2563eb;
    }

    .stProgress > div > div > div > div {
        background-color: #3b82f6;
        border-radius: 10px;
    }

    .st-expander {
        background-color: #f3f4f6;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }

    .st-expander-header {
        font-weight: bold;
        font-size: 1.2em;
        color: #111827;
    }

    .st-expander-content {
        font-size: 1rem;
        color: #4b5563;
        padding-top: 0.75rem;
    }
    
    </style>
    """, unsafe_allow_html=True)


def render_choose_method():
    st.title("AI Hypotheek Assistent")
    
    st.markdown("<p>Kies een methode om te beginnen:</p>", unsafe_allow_html=True)
    
    # Use columns to arrange the buttons horizontally
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("📝 Handmatige Invoer", use_container_width=True):
            st.session_state.upload_method = "manual"
            st.session_state.step = "upload"
            st.rerun()
    with col2:
        if st.button("📁 Bestand Uploaden", use_container_width=True):
            st.session_state.upload_method = "file"
            st.session_state.step = "upload"
            st.rerun()
    with col3:
        if st.button("🎙️ Audio Opnemen", use_container_width=True):
            st.session_state.upload_method = "audio"
            st.session_state.step = "upload"
            st.rerun()





def render_upload(gpt_service, audio_service, transcription_service):
    st.title("Transcript Invoer")
    transcript = None

    # Ensure upload_method is initialized
    if 'upload_method' not in st.session_state:
        st.session_state.upload_method = None

    if st.session_state.upload_method == "manual":
        transcript = st.text_area("Voer het transcript in:", height=300)
        if st.button("Analyseer", use_container_width=True):
            process_transcript(transcript, gpt_service)

    elif st.session_state.upload_method == "file":
        uploaded_file = st.file_uploader("Kies een bestand", type=["txt", "docx", "wav", "mp3", "m4a"])
        if uploaded_file:
            st.write(f"File name: {uploaded_file.name}")
            st.write(f"File type: {uploaded_file.type}")
            st.write(f"File size: {uploaded_file.size} bytes")
            
            if uploaded_file.type.startswith('audio') or uploaded_file.name.lower().endswith(('.wav', '.mp3', '.m4a')):
                with st.spinner("Audio wordt getranscribeerd..."):
                    transcript = transcription_service.transcribe(uploaded_file)
            else:
                transcript = uploaded_file.getvalue().decode("utf-8")
            
            if transcript:
                st.success("Bestand succesvol verwerkt.")
                st.write("Transcript:")
                st.text_area("Edit transcript if needed:", value=transcript, height=300, key="editable_transcript")
                if st.button("Analyseer", use_container_width=True):
                    process_transcript(st.session_state.editable_transcript, gpt_service)
            else:
                st.error("Er is een fout opgetreden bij het verwerken van het bestand.")

    else:  # audio recording
        audio_bytes = audio_service.record_audio()
        if audio_bytes:
            with st.spinner("Audio wordt getranscribeerd..."):
                transcript = transcription_service.transcribe(audio_bytes)
            
            if transcript:
                st.success("Audio succesvol opgenomen en getranscribeerd.")
                st.write("Transcript:")
                st.text_area("Edit transcript if needed:", value=transcript, height=300, key="editable_transcript")
                if st.button("Analyseer", use_container_width=True):
                    process_transcript(st.session_state.editable_transcript, gpt_service)
            else:
                st.error("Er is een fout opgetreden bij het transcriberen van de audio.")

def process_transcript(transcript, gpt_service):
    if transcript:
        with st.spinner("Bezig met analyseren..."):
            result = gpt_service.analyze_transcript(transcript)
        st.session_state.result = result
        st.session_state.transcript = transcript
        st.session_state.step = "results"
        st.rerun()
    else:
        st.error("Er is geen transcript om te analyseren. Voer een transcript in, upload een bestand, of neem audio op.")

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
        
        if st.button("Exporteer als Word-document", use_container_width=True):
            export_to_docx(result)  # Directly call the export function to trigger download
    else:
        st.warning("Er zijn geen resultaten beschikbaar.")
    
    render_feedback_section()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Terug naar Start", use_container_width=True):
            st.session_state.step = "choose_method"
            st.rerun()
    with col2:
        if st.button("Nieuwe Analyse", use_container_width=True):
            st.session_state.clear()
            st.rerun()

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
        {st.session_state.get('transcript', 'Geen transcript beschikbaar')}

        Output:
        {st.session_state.get('result', 'Geen resultaten beschikbaar')}
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
    from docx import Document
    from io import BytesIO
    
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