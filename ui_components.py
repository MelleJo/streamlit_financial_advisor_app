import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from docx import Document
from io import BytesIO
import logging
import re
from definitions import MORTGAGE_DEFINITIONS, improve_explanation

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
    
    .term-button {
        display: inline-block;
        background-color: #E8F0FE;
        padding: 2px 8px;
        border-radius: 4px;
        color: #1a73e8;
        font-weight: 500;
        border: none;
        margin: 0 2px;
        cursor: pointer;
        text-decoration: none;
        transition: all 0.2s ease;
    }

    .term-button:hover {
        background-color: #d2e3fc;
    }

    .explanation-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .explanation-title {
        color: #1a73e8;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        font-weight: 500;
    }

    .explanation-content {
        color: #333;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

def render_progress_bar(app_state):
    steps = {
        "select_persons": "Personen",
        "person_details": "Gegevens",
        "choose_method": "Methode",
        "upload": "Invoer",
        "results": "Resultaten"
    }
    current_step = app_state.step
    step_list = list(steps.keys())
    current_step_index = step_list.index(current_step)
    progress = (current_step_index + 1) / len(steps)
    
    st.progress(progress)
    cols = st.columns(len(steps))
    for i, (step, label) in enumerate(steps.items()):
        with cols[i]:
            if step_list.index(step) < current_step_index:
                st.markdown(f"✅ {label}")
            elif step == current_step:
                st.markdown(f"**🔵 {label}**")
            else:
                st.markdown(f"⚪ {label}")

def render_choose_method(app_state):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Handmatige invoer", use_container_width=True):
            app_state.set_upload_method("manual")
            app_state.set_step("upload")
    with col2:
        if st.button("📁 Bestand uploaden", use_container_width=True):
            app_state.set_upload_method("file")
            app_state.set_step("upload")
    with col3:
        if st.button("🎙️ Audio opnemen", use_container_width=True):
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
                # Clean the content before displaying
                cleaned_content = clean_text_content(content)
                format_text_with_definitions(cleaned_content, section)
        
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

def render_person_selection(app_state):
    st.title("Personen Selectie")
    st.write("Selecteer het aantal personen voor het hypotheekadvies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        number_of_persons = st.radio(
            "Aantal personen",
            options=[1, 2],
            format_func=lambda x: f"{x} {'persoon' if x == 1 else 'personen'}"
        )
        
        if st.button("Bevestig aantal personen", use_container_width=True):
            app_state.set_number_of_persons(number_of_persons)
            app_state.set_step("person_details")
            
    with col2:
        st.info("""
        💡 Tip: Selecteer het aantal personen dat betrokken is bij de hypotheekaanvraag. 
        Dit helpt ons om een gepersonaliseerd advies te geven voor elk scenario.
        """)

def render_person_details(app_state):
    st.title("Persoonlijke Gegevens")
    st.write("Vul de gegevens in voor alle betrokken personen")
    
    all_filled = True
    
    for person_id, details in app_state.person_details.items():
        person_number = person_id.split("_")[1]
        with st.expander(f"Persoon {person_number}", expanded=True):
            name = st.text_input(
                "Naam",
                key=f"{person_id}_name",
                value=details.get("name", "")
            )
            
            employment_status = st.selectbox(
                "Arbeidssituatie",
                options=["Loondienst", "Zelfstandig", "Werkloos", "Pensioen"],
                key=f"{person_id}_employment",
                index=None
            )
            
            if employment_status in ["Loondienst", "Zelfstandig"]:
                income = st.number_input(
                    "Jaarinkomen",
                    min_value=0,
                    max_value=1000000,
                    step=1000,
                    key=f"{person_id}_income",
                    format="%d"
                )
            else:
                income = 0
            
            pension_status = st.selectbox(
                "Pensioensituatie",
                options=["Nog niet in pensioen", "Bijna in pensioen", "In pensioen"],
                key=f"{person_id}_pension",
                index=None
            )
            
            app_state.set_person_detail(person_id, "name", name)
            app_state.set_person_detail(person_id, "employment_status", employment_status)
            app_state.set_person_detail(person_id, "pension_status", pension_status)
            app_state.set_person_detail(person_id, "income", income)
            
            if not name or not employment_status or not pension_status:
                all_filled = False
    
    if st.button("Ga door naar advies", use_container_width=True):
        if all_filled:
            app_state.set_step("choose_method")
        else:
            st.error("Vul alstublieft alle verplichte velden in voordat u doorgaat.")

def clean_text_content(text):
    """Clean and format text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Ensure proper sentence spacing
    text = re.sub(r'([.!?])\s*', r'\1\n', text)
    # Clean up bullet points
    text = re.sub(r'\n\s*•\s*', '\n• ', text)
    # Remove empty lines
    text = '\n'.join(line for line in text.split('\n') if line.strip())
    return text.strip()

def format_text_with_definitions(text, section_key):
    """Format text by highlighting defined terms and making them clickable."""
    if not text:
        return text

    # Add custom CSS for the term highlighting
    st.markdown("""
        <style>
        span.term {
            background-color: #E8F0FE;
            padding: 2px 8px;
            border-radius: 4px;
            color: #1a73e8;
            font-weight: 500;
            cursor: pointer;
            margin: 0 2px;
            display: inline-block;
            font-size: 0.9em;
            border: 1px solid #d2e3fc;
            line-height: normal;
        }
        
        span.term:hover {
            background-color: #d2e3fc;
        }
        
        .text-paragraph {
            line-height: 1.6;
            margin-bottom: 1em;
            color: #1f2937;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    if 'selected_term' not in st.session_state:
        st.session_state.selected_term = None
        st.session_state.selected_section = None
    
    with col1:
        text = clean_text_content(text)
        
        # Process text paragraph by paragraph
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                continue
            
            # Create a container for this paragraph's clickable terms
            for term in MORTGAGE_DEFINITIONS.keys():
                term_key = f"{term}_{section_key}_{hash(paragraph)}"
                # Create a small clickable element for each term
                if term.lower() in paragraph.lower():
                    if st.button(term, key=term_key, help="Klik voor uitleg"):
                        st.session_state.selected_term = term
                        st.session_state.selected_section = section_key
            
            # Display the actual paragraph
            st.markdown(f'<p class="text-paragraph">{paragraph}</p>', unsafe_allow_html=True)
    
    with col2:
        if (st.session_state.selected_term and 
            st.session_state.selected_section == section_key):
            
            st.markdown(f"""
                <div style="background-color: white; 
                           padding: 1rem; 
                           border-radius: 8px; 
                           border: 1px solid #e0e0e0;
                           margin-bottom: 1rem;
                           box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h4 style="color: #1a73e8; 
                             margin-bottom: 0.5rem; 
                             font-size: 1rem;">
                        📚 {st.session_state.selected_term}
                    </h4>
                    <div style="color: #374151; 
                              font-size: 0.95rem; 
                              line-height: 1.6;">
                        {MORTGAGE_DEFINITIONS[st.session_state.selected_term].replace('\n', '<br>')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(
                "➕ Voeg uitleg toe", 
                type="primary",
                use_container_width=True,
                key=f"add_{section_key}_{st.session_state.selected_term}"
            ):
                enhanced_text = improve_explanation(
                    st.session_state.selected_term,
                    MORTGAGE_DEFINITIONS[st.session_state.selected_term],
                    text,
                    st.session_state.openai_client
                )
                
                if enhanced_text:
                    st.session_state.enhanced_texts[section_key] = enhanced_text
                    if hasattr(st.session_state, 'app_state'):
                        if section_key in st.session_state.app_state.result:
                            st.session_state.app_state.result[section_key] = enhanced_text
                            st.rerun()
