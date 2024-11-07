import streamlit as st
from datetime import datetime

def render_chat_message(message, is_ai):
    """Render a single chat message with custom styling"""
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
                <p style="margin: 5px 0 0 0; color: #333;">{message}</p>
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
                <p style="margin: 5px 0 0 0; color: #333;">{message}</p>
            </div>
        """, unsafe_allow_html=True)

def render_conversation_ui(app_state, conversation_service):
    st.markdown("""
        <style>
        .chat-container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # Chat history container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Render conversation history
    for message in app_state.conversation_history:
        render_chat_message(message["content"], message["is_ai"])
    
    # User input
    user_input = st.text_input(
        "",
        key="user_input",
        placeholder="Typ uw antwoord hier...",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([6,1])
    with col2:
        send_button = st.button("📤 Verstuur", use_container_width=True)

    if send_button and user_input:
        # Add user message to history
        app_state.add_message(user_input, is_ai=False)
        
        # Process response
        response = conversation_service.process_user_response(
            conversation_service.format_conversation_history(app_state.conversation_history),
            user_input,
            app_state.missing_info
        )
        
        if response:
            # Add AI response to history
            if response.get("next_question"):
                context = response.get("context", "")
                message = f"{response['next_question']}\n\n{context if context else ''}"
                app_state.add_message(message, is_ai=True)
            
            # Update missing info
            if response.get("remaining_missing_info"):
                app_state.set_missing_info(response["remaining_missing_info"])
            
            # Check if all information is collected
            if not response.get("remaining_missing_info"):
                app_state.set_analysis_complete(True)
                app_state.set_step("results")
                st.rerun()
        
        # Clear input
        st.session_state.user_input = ""
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)