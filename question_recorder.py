import streamlit as st
from streamlit_mic_recorder import mic_recorder
from typing import List, Dict, Any, Callable
from transcription_service import TranscriptionService

QUESTIONS = [
    {
        "question": "Wat is het gewenste leningbedrag van uw cliënt?",
        "context": "Noteer het bedrag dat de cliënt wil lenen voor de hypotheek.",
        "category": "leningdeel"
    },
    {
        "question": "Heeft uw cliënt interesse in NHG (Nationale Hypotheek Garantie)?",
        "context": "Bespreek of de cliënt gebruik wil maken van NHG en waarom.",
        "category": "leningdeel"
    },
    {
        "question": "Welke hypotheekvorm heeft uw cliënt gekozen?",
        "context": "Annuïteit, lineair of een andere vorm - inclusief motivatie.",
        "category": "leningdeel"
    },
    {
        "question": "Welke rentevaste periode wenst uw cliënt?",
        "context": "Bespreek de gekozen periode en de overwegingen daarbij.",
        "category": "leningdeel"
    },
    {
        "question": "Wat is de arbeidssituatie van uw cliënt en hoe kijkt deze aan tegen werkloosheidsrisico's?",
        "context": "Huidige arbeidscontract, sector, en risico-inschatting.",
        "category": "werkloosheid"
    },
    {
        "question": "Wat zijn de wensen van uw cliënt voor de hypotheek na pensionering?",
        "context": "Bespreek de AOW-leeftijd, pensioenopbouw en gewenste situatie.",
        "category": "aow"
    }
]

def render_question_recorder(
    transcription_service: TranscriptionService,
    on_complete: Callable[[Dict[str, str]], None],
    on_skip: Callable[[], None]
):
    """Renders an interface for recording answers to all questions at once."""
    
    st.markdown("""
        <style>
        .question-list {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 2rem;
        }
        .question-item {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            transition: all 0.2s ease;
        }
        .question-item:hover {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            transform: translateY(-2px);
        }
        .question-number {
            color: #1a73e8;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .question-text {
            color: #1f2937;
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .question-context {
            color: #6b7280;
            font-size: 0.9rem;
            font-style: italic;
        }
        .recording-section {
            background: #f8fafc;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 📝 Adviesnotities opnemen")
    st.markdown("""
        Hieronder ziet u alle onderwerpen die aan bod moeten komen in uw advies. 
        U kunt uw complete adviesnotitie in één keer opnemen.
    """)

    # Display all questions
    st.markdown('<div class="question-list">', unsafe_allow_html=True)
    for i, q in enumerate(QUESTIONS, 1):
        st.markdown(f"""
            <div class="question-item">
                <div class="question-number">Onderwerp {i}</div>
                <div class="question-text">{q['question']}</div>
                <div class="question-context">{q['context']}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Recording section
    st.markdown('<div class="recording-section">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🎙️ Neem uw adviesnotitie op")
        audio = mic_recorder(
            start_prompt="Start Opname",
            stop_prompt="Stop Opname",
            key="full_recording"
        )

    with col2:
        if st.button("🏁 Sla opname over", use_container_width=True, type="secondary"):
            on_skip()
    
    st.markdown('</div>', unsafe_allow_html=True)

    if audio:
        with st.spinner("Uw opname wordt verwerkt..."):
            # Create a prompt that includes all questions
            context_prompt = "Hypotheekadvies notitie met de volgende onderwerpen: " + \
                           "; ".join(q['question'] for q in QUESTIONS)
            
            transcript = transcription_service.transcribe(
                audio['bytes'],
                mode="accurate",
                prompt=context_prompt
            )
            
            if transcript:
                result = {
                    "full_recording": transcript,
                    "questions": QUESTIONS
                }
                on_complete(result)
                st.rerun()