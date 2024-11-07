"""
File: conversation_ui.py
Handles the chat interface UI components for the AI Hypotheek Assistent.
This module provides functions to render and manage the chat interface,
including message display, user input handling, and conversation flow.
It implements a custom styled chat UI with distinct message bubbles for
user and AI responses, along with real-time message processing.
"""

import streamlit as st
import json
from typing import Dict, Any
from app_state import AppState

def render_chat_message(message: Dict[str, Any]):
    """Render a single chat message with custom styling and context"""
    is_ai = message.get("is_ai", False)
    content = message.get("content", "")
    context = message.get("context", "")
    
    if is_ai:
        st.markdown(f"""
            <div style="
                background-color: #E8F0FE;
                border-radius: 15px;
                padding: 10px 15px;
                margin: 5px 0;
                max-width: 80%;
                margin-right: 20%;
            ">
                <p style="margin: 0; color: #1a73e8;">🤖 AI Adviseur</p>
                {f'<p style="margin: 5px 0; color: #666; font-size: 0.9em; font-style: italic;">{context}</p>' if context else ''}
                <p style="margin: 5px 0 0 0; color: #333;">{content}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="
                background-color: #F8F9FA;
                border-radius: 15px;
                padding: 10px 15px;
                margin: 5px 0;
                max-width: 80%;
                margin-left: 20%;
            ">
                <p style="margin: 0; color: #666;">👤 U</p>
                <p style="margin: 5px 0 0 0; color: #333;">{content}</p>
            </div>
        """, unsafe_allow_html=True)

def render_progress_indicator(app_state: 'AppState'):
    """Render progress indicator showing completed and remaining topics"""
    if app_state.remaining_topics:
        st.markdown("### 📊 Voortgang")
        
        total_topics = sum(len(topics) for topics in app_state.missing_info.values())
        remaining_topics = sum(len(topics) for topics in app_state.remaining_topics.values())
        completed_topics = total_topics - remaining_topics
        
        progress = completed_topics / total_topics if total_topics > 0 else 0
        st.progress(progress)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Behandeld:** {completed_topics}/{total_topics}")
        with col2:
            st.markdown(f"**Nog te bespreken:** {remaining_topics}")
        
        # Show remaining topics by category
        with st.expander("📋 Nog te bespreken onderwerpen", expanded=False):
            for category, topics in app_state.remaining_topics.items():
                category_titles = {
                    'leningdeel': '💰 Leningdeel',
                    'werkloosheid': '🏢 Werkloosheid',
                    'aow': '👴 AOW & Pensioen'
                }
                st.markdown(f"**{category_titles.get(category, category)}**")
                for topic in topics:
                    st.markdown(f"- {topic}")

def render_conversation_ui(app_state: 'AppState', conversation_service: Any):
    """Render the conversation interface"""
    
    # Initialize session state for message handling
    if 'message_sent' not in st.session_state:
        st.session_state.message_sent = False
    
    st.markdown("""
        <style>
        .chat-container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stTextInput>div>div>input {
            border-radius: 20px;
            border: 2px solid #E8F0FE;
            padding: 10px 20px;
        }
        .stTextInput>div>div>input:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
        }
        .topic-progress {
            padding: 10px;
            background-color: #F8F9FA;
            border-radius: 8px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Show progress indicator
    render_progress_indicator(app_state)

    # Original transcript expander
    if app_state.transcript:
        with st.expander("📝 Oorspronkelijk transcript", expanded=False):
            st.markdown(f"```{app_state.transcript}```")

    # Chat history container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Render conversation history with context
    for message in app_state.conversation_history:
        render_chat_message(message)
    
    # User input area
    col1, col2 = st.columns([6,1])
    
    with col1:
        user_input = st.text_input(
            "Uw antwoord",  # Added label for accessibility
            key="user_input",
            placeholder="Typ uw antwoord hier...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Verstuur", use_container_width=True)

    # Process user input
    if send_button and user_input and not st.session_state.message_sent:
        st.session_state.message_sent = True
        
        # Add user message to history
        app_state.add_message(user_input, is_ai=False)
        
        # Process response
        conversation_history = conversation_service.format_conversation_history(
            app_state.conversation_history
        )
        
        with st.spinner("Even denken..."):
            response = conversation_service.process_user_response(
                conversation_history,
                user_input,
                app_state.remaining_topics
            )
        
        if response:
            # Add AI response to history
            if response.get("next_question"):
                context = response.get("context", "")
                app_state.add_message(
                    response["next_question"],
                    is_ai=True,
                    context=context
                )
            
            # Update remaining topics
            remaining_missing_info = response.get("remaining_missing_info")
            if remaining_missing_info is not None:
                app_state.remaining_topics = remaining_missing_info
            
            # Add Q&A pair to structured history
            if response.get("processed_info"):
                category = next(iter(response["processed_info"]))  # Get the category that was just discussed
                app_state.add_qa_pair(
                    response["next_question"],
                    user_input,
                    response.get("context", ""),
                    category
                )
            
            # Check if all information is collected
            if not remaining_missing_info:
                app_state.set_analysis_complete(True)
                app_state.set_step("results")
        
        st.rerun()
    
    # Reset message_sent state if needed
    if not send_button:
        st.session_state.message_sent = False
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Debug information in expander (optional)
    with st.expander("Debug Informatie", expanded=False):
        st.write("Remaining Topics:", app_state.remaining_topics)
        st.write("Structured Q&A History:", app_state.structured_qa_history)
