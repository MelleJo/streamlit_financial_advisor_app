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
        .missing-topics {
            background-color: #fff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .topic-section {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 8px;
            background-color: #f8f9fa;
        }
        .topic-title {
            font-weight: 600;
            color: #1a73e8;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .topic-item {
            padding: 8px 12px;
            background-color: #fff;
            border-radius: 6px;
            margin-bottom: 8px;
            border-left: 3px solid #dc2626;
        }
        .recording-section {
            background-color: #f8fafc;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid #e5e7eb;
        }
        .instruction-text {
            color: #374151;
            font-style: italic;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #e8f0fe;
            border-radius: 6px;
        }
        .explanation-text {
            padding: 10px;
            background-color: #fff3ed;
            border-radius: 6px;
            margin-bottom: 15px;
            color: #b45309;
        }
        .question-text {
            font-size: 1.1em;
            color: #1a73e8;
            margin-bottom: 15px;
            padding: 15px;
            background-color: #f0f7ff;
            border-radius: 8px;
            border-left: 4px solid #1a73e8;
        }
        .context-text {
            color: #6b7280;
            font-size: 0.9em;
            margin-bottom: 10px;
            padding: 8px;
            background-color: #f9fafb;
            border-radius: 6px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize conversation service if not already in session state
    if 'conversation_service' not in st.session_state:
        st.session_state.conversation_service = ConversationService(st.secrets.API.get("OPENAI_API_KEY"))
    
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
        st.markdown("### 📋 Overzicht Ontbrekende Informatie")
        st.markdown('<div class="missing-topics">', unsafe_allow_html=True)
        
        if explanation:
            st.markdown(f'<div class="explanation-text">{explanation}</div>', unsafe_allow_html=True)
        
        for section, topics in missing_topics.items():
            if topics:  # Only show sections with missing topics
                st.markdown(f'<div class="topic-section">', unsafe_allow_html=True)
                section_titles = {
                    'leningdeel': '💰 Leningdeel',
                    'werkloosheid': '🏢 Werkloosheid',
                    'aow': '👴 AOW & Pensioen'
                }
                st.markdown(f'<div class="topic-title">{section_titles.get(section, section.capitalize())}</div>', unsafe_allow_html=True)
                for topic in topics:
                    st.markdown(f'<div class="topic-item">❌ {topic}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Get next question from conversation service
        conversation_result = st.session_state.conversation_service.process_user_response(
            "\n".join(st.session_state.conversation_history),
            st.session_state.current_transcript,
            missing_topics
        )
        
        next_question = conversation_result["next_question"]
        context = conversation_result["context"]
        
        st.markdown("### 🎙️ Volgende Vraag")
        st.markdown('<div class="recording-section">', unsafe_allow_html=True)
        
        st.markdown(f'<div class="context-text">{context}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="question-text">{next_question}</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2,1])
        
        with col1:
            audio = mic_recorder(
                start_prompt="Start Opname",
                stop_prompt="Stop Opname",
                key="single_question"
            )

        with col2:
            if st.button("⏩ Sla Vraag Over", use_container_width=True, type="secondary"):
                on_skip()
        
        if audio:
            with st.spinner("Opname wordt verwerkt..."):
                answer_transcript = transcription_service.transcribe(
                    audio['bytes'],
                    mode="accurate",
                    language="nl"
                )
                
                if answer_transcript:
                    st.success("✅ Antwoord verwerkt!")
                    
                    # Update conversation history
                    st.session_state.conversation_history.append(f"AI: {next_question}")
                    st.session_state.conversation_history.append(f"Klant: {answer_transcript}")
                    
                    # Update current transcript
                    st.session_state.current_transcript = (
                        f"{st.session_state.current_transcript}\n\n"
                        f"Vraag: {next_question}\n"
                        f"Antwoord: {answer_transcript}"
                    )
                    
                    # Reanalyze to check remaining missing information
                    final_analysis = checklist_service.analyze_transcript(st.session_state.current_transcript)
                    
                    if not final_analysis.get('missing_topics'):
                        st.success("🎯 Alle benodigde informatie is nu compleet!")
                        on_complete({
                            'transcript': st.session_state.current_transcript,
                            'conversation_history': st.session_state.conversation_history,
                            'missing_topics': {}
                        })
                    else:
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
