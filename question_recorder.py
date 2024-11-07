import streamlit as st
from streamlit_mic_recorder import mic_recorder
from typing import List, Dict, Any, Callable
from transcription_service import TranscriptionService

def render_question_recorder(
    questions: List[Dict[str, str]],
    transcription_service: TranscriptionService,
    on_complete: Callable[[Dict[int, Dict[str, str]]], None],
    on_skip: Callable[[], None]
):
    """Renders the question recording interface with audio recording and transcription."""
    
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'recording_state' not in st.session_state:
        st.session_state.recording_state = 'ready'

    st.markdown("""
        <style>
        .question-container {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(226, 232, 240, 0.8);
        }
        .question-header {
            color: #1a73e8;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .question-text {
            color: #1f2937;
            font-size: 1.2rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }
        .question-context {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 1rem;
            font-style: italic;
        }
        .progress-bar {
            margin: 2rem 0;
            padding: 1rem;
            background: #f1f5f9;
            border-radius: 10px;
        }
        .recording-section {
            margin-top: 2rem;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Progress bar
    progress = st.session_state.current_question_index / len(questions)
    st.progress(progress, "Voortgang")

    # Current question
    if st.session_state.current_question_index < len(questions):
        current_question = questions[st.session_state.current_question_index]
        
        st.markdown(f"""
            <div class="question-container">
                <div class="question-header">Vraag {st.session_state.current_question_index + 1} van {len(questions)}</div>
                <div class="question-text">{current_question['question']}</div>
                <div class="question-context">{current_question.get('context', '')}</div>
            </div>
        """, unsafe_allow_html=True)

        # Recording interface
        st.markdown('<div class="recording-section">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            audio = mic_recorder(
                start_prompt="🎙️ Start Opname",
                stop_prompt="⏹️ Stop Opname",
                key=f"recorder_{st.session_state.current_question_index}"
            )

        with col2:
            if st.button("⏭️ Sla deze vraag over", use_container_width=True):
                st.session_state.current_question_index += 1
                if st.session_state.current_question_index >= len(questions):
                    on_complete(st.session_state.answers)
                st.rerun()

        with col3:
            if st.button("🏁 Beëindig opname", use_container_width=True, type="primary"):
                on_skip()

        st.markdown('</div>', unsafe_allow_html=True)

        if audio and st.session_state.recording_state != 'processing':
            st.session_state.recording_state = 'processing'
            with st.spinner("Audio wordt verwerkt..."):
                transcript = transcription_service.transcribe(
                    audio['bytes'],
                    mode="accurate",
                    prompt=current_question['question']
                )
                
                if transcript:
                    st.session_state.answers[st.session_state.current_question_index] = {
                        'question': current_question['question'],
                        'answer': transcript
                    }
                    st.session_state.current_question_index += 1
                    st.session_state.recording_state = 'ready'
                    
                    if st.session_state.current_question_index >= len(questions):
                        on_complete(st.session_state.answers)
                    st.rerun()

        # Show recorded answers
        if st.session_state.answers:
            with st.expander("📝 Bekijk gegeven antwoorden"):
                for idx, answer in st.session_state.answers.items():
                    st.markdown(f"""
                        **Vraag {idx + 1}:** {answer['question']}  
                        *Antwoord:* {answer['answer']}
                    """)