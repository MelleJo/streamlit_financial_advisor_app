"""
File: question_recorder.py
Implements an intelligent question recording interface based on checklist analysis.
"""

import streamlit as st
from streamlit_mic_recorder import mic_recorder
from typing import Dict, Any, Callable
import asyncio
from checklist_analysis_service import ChecklistAnalysisService, CHECKLIST_SECTIONS

def render_question_recorder(
    transcription_service,
    checklist_service: ChecklistAnalysisService,
    on_complete: Callable[[Dict[str, str]], None],
    on_skip: Callable[[], None],
    initial_transcript: str
):
    """Renders an intelligent question recording interface based on checklist analysis."""
    
    # Initialize session state for tracking questions and answers
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'answers' not in st.session_state:
        st.session_state.answers = []
    if 'missing_points' not in st.session_state:
        # Analyze initial transcript when first loading
        analysis_result = asyncio.run(checklist_service.analyze_transcript(initial_transcript))
        st.session_state.missing_points = analysis_result.get('missing_points', {})
        st.session_state.current_question = analysis_result.get('next_questions', [{}])[0]

    # Custom CSS for better visual hierarchy
    st.markdown("""
        <style>
        .checklist-container {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 1.5rem;
        }
        .checklist-section {
            margin-bottom: 1rem;
        }
        .checklist-section-title {
            font-weight: 600;
            color: #1a73e8;
            margin-bottom: 0.5rem;
        }
        .checklist-item {
            display: flex;
            align-items: center;
            padding: 0.5rem;
            border-radius: 4px;
        }
        .checklist-item.missing {
            background-color: #fef2f2;
        }
        .checklist-item.complete {
            background-color: #f0fdf4;
        }
        .question-container {
            background: #f8fafc;
            padding: 1.5rem;
            border-radius: 10px;
            margin-top: 1.5rem;
        }
        .context-box {
            background: #e8f0fe;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            font-style: italic;
            color: #1e40af;
        }
        </style>
    """, unsafe_allow_html=True)

    # Show checklist progress
    st.markdown("### 📋 Voortgang Checklist")
    
    with st.expander("Bekijk voortgang", expanded=True):
        st.markdown('<div class="checklist-container">', unsafe_allow_html=True)
        
        for section, points in CHECKLIST_SECTIONS.items():
            st.markdown(f'<div class="checklist-section">', unsafe_allow_html=True)
            st.markdown(f'<div class="checklist-section-title">{section.capitalize()}</div>', unsafe_allow_html=True)
            
            for point in points:
                is_missing = point in st.session_state.missing_points.get(section, [])
                status_class = "missing" if is_missing else "complete"
                icon = "❌" if is_missing else "✅"
                
                st.markdown(
                    f'<div class="checklist-item {status_class}">{icon} {point}</div>',
                    unsafe_allow_html=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Show current question and recording interface
    if st.session_state.current_question:
        st.markdown("### 🎙️ Volgende Vraag")
        st.markdown('<div class="question-container">', unsafe_allow_html=True)
        
        # Show question context
        if st.session_state.current_question.get('context'):
            st.markdown(
                f'<div class="context-box">{st.session_state.current_question["context"]}</div>',
                unsafe_allow_html=True
            )
        
        # Show the question
        st.write(f"**{st.session_state.current_question['question']}**")
        
        # Recording interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            audio = mic_recorder(
                start_prompt="Start Opname",
                stop_prompt="Stop Opname",
                key="answer_recording"
            )

        with col2:
            if st.button("➡️ Volgende Vraag", use_container_width=True):
                # Generate next question
                next_question = asyncio.run(checklist_service.generate_next_question(
                    st.session_state.missing_points,
                    st.session_state.answers
                ))
                
                if next_question.get('question'):
                    st.session_state.current_question = next_question
                else:
                    # No more questions needed
                    on_complete({
                        'answers': st.session_state.answers,
                        'missing_points': st.session_state.missing_points
                    })
                st.rerun()

        # Process recorded answer
        if audio:
            with st.spinner("Antwoord wordt verwerkt..."):
                transcript = transcription_service.transcribe(
                    audio['bytes'],
                    mode="accurate",
                    language="nl",
                    prompt=st.session_state.current_question['question']
                )
                
                if transcript:
                    # Store the answer
                    st.session_state.answers.append({
                        'question': st.session_state.current_question['question'],
                        'answer': transcript,
                        'related_points': st.session_state.current_question.get('related_points', [])
                    })
                    
                    # Update missing points
                    for point in st.session_state.current_question.get('related_points', []):
                        for section in st.session_state.missing_points:
                            if point in st.session_state.missing_points[section]:
                                st.session_state.missing_points[section].remove(point)
                    
                    # Get next question
                    next_question = asyncio.run(checklist_service.generate_next_question(
                        st.session_state.missing_points,
                        st.session_state.answers
                    ))
                    
                    if next_question.get('question'):
                        st.session_state.current_question = next_question
                    else:
                        # No more questions needed
                        on_complete({
                            'answers': st.session_state.answers,
                            'missing_points': st.session_state.missing_points
                        })
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Skip button
    if st.button("🏁 Afronden", use_container_width=True, type="secondary"):
        on_skip()