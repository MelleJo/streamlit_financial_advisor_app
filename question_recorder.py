"""
File: question_recorder.py
Handles the interactive question and answer session for gathering missing information.
"""
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from typing import Dict, Any, Callable
from conversation_service import ConversationService

def render_question_recorder(
    transcription_service,
    checklist_service,
    on_complete: Callable[[Dict[str, str]], None],
    on_skip: Callable[[], None],
    initial_transcript: str
):
    """Renders an intelligent question recording interface for missing information."""
    
    st.markdown("""
        <style>
        .question-group {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .question-item {
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 3px solid #1a73e8;
        }
        .question-context {
            color: #666;
            font-size: 0.9em;
            font-style: italic;
            margin-bottom: 8px;
        }
        .question-text {
            color: #1a73e8;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        .recording-controls {
            background-color: #e8f0fe;
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize conversation service if not already in session state
    if 'conversation_service' not in st.session_state:
        st.session_state.conversation_service = ConversationService(st.secrets["OPENAI_API_KEY"])
    
    # Initialize conversation history if not already in session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
        st.session_state.current_transcript = initial_transcript

    # Show original transcript in expander
    with st.expander("📝 Oorspronkelijk transcript", expanded=False):
        st.markdown(f"```{initial_transcript}```")

    # Analyze transcript using checklist service
    with st.spinner("Transcript wordt geanalyseerd..."):
        analysis = checklist_service.analyze_transcript(st.session_state.current_transcript)
    
    missing_topics = analysis.get('missing_topics', {})
    explanation = analysis.get('explanation', '')
    
    if not missing_topics:
        st.success("✅ Alle benodigde informatie is aanwezig!")
        if st.button("➡️ Doorgaan naar Analyse", use_container_width=True):
            on_complete({
                'transcript': st.session_state.current_transcript,
                'conversation_history': st.session_state.conversation_history
            })
    else:
        # Get all questions from conversation service
        conversation_result = st.session_state.conversation_service.process_user_response(
            "\n".join(st.session_state.conversation_history),
            st.session_state.current_transcript,
            missing_topics
        )
        
        st.markdown("### 📋 Resterende Vragen")
        
        # Display all questions
        st.markdown('<div class="question-group">', unsafe_allow_html=True)
        
        if explanation:
            st.info(explanation)
        
        questions = conversation_result.get("questions", [])
        if not questions:
            st.success("🎯 Alle benodigde informatie is nu compleet!")
            on_complete({
                'transcript': st.session_state.current_transcript,
                'conversation_history': st.session_state.conversation_history
            })
        else:
            for idx, q in enumerate(questions):
                st.markdown(f"""
                    <div class="question-item">
                        <div class="question-context">{q['context']}</div>
                        <div class="question-text">{q['question']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Single recording section for all questions
            st.markdown("### 🎙️ Neem je antwoord op")
            st.markdown("""
                <div class="recording-controls">
                    <p>Beantwoord alsjeblieft alle bovenstaande vragen in je opname. 
                    Je kunt ze één voor één behandelen of in een doorlopend antwoord.</p>
                </div>
            """, unsafe_allow_html=True)
            
            audio = mic_recorder(
                start_prompt="Start Opname",
                stop_prompt="Stop Opname",
                key="batch_questions"
            )
            
            col1, col2 = st.columns([2,1])
            
            with col2:
                if st.button("⏩ Sla Vragen Over", use_container_width=True, type="secondary"):
                    on_skip()
            
            if audio:
                with st.spinner("Opname wordt verwerkt..."):
                    answer_transcript = transcription_service.transcribe(
                        audio['bytes'],
                        mode="accurate",
                        language="nl"
                    )
                    
                    if answer_transcript:
                        st.success("✅ Antwoorden verwerkt!")
                        
                        # Update conversation history with all questions and the single answer
                        for q in questions:
                            st.session_state.conversation_history.append(f"AI: {q['question']}")
                        st.session_state.conversation_history.append(f"Klant: {answer_transcript}")
                        
                        # Update current transcript
                        st.session_state.current_transcript = (
                            f"{st.session_state.current_transcript}\n\n"
                            f"Vragen:\n" + "\n".join(q['question'] for q in questions) + "\n"
                            f"Antwoord:\n{answer_transcript}"
                        )
                        
                        # Reanalyze to check remaining missing information
                        final_analysis = checklist_service.analyze_transcript(
                            st.session_state.current_transcript
                        )
                        
                        if not final_analysis.get('missing_topics'):
                            st.success("🎯 Alle benodigde informatie is nu compleet!")
                            on_complete({
                                'transcript': st.session_state.current_transcript,
                                'conversation_history': st.session_state.conversation_history
                            })
                        else:
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
