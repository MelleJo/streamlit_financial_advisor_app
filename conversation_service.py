import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
import logging
import json
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_RESPONSE = {
    "complete_info": {"leningdeel": {}, "werkloosheid": {}, "aow": {}},
    "missing_info": {
        "leningdeel": ["Basisinformatie ontbreekt"],
        "werkloosheid": ["Basisinformatie ontbreekt"],
        "aow": ["Basisinformatie ontbreekt"]
    },
    "next_question": "Kunt u mij vertellen wat het gewenste leningbedrag is?",
    "context": "We beginnen met de basisinformatie voor uw hypotheekaanvraag."
}

class ConversationService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-08-06",
            temperature=0.3,
            openai_api_key=api_key
        )
        
        # Analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die transcripten analyseert. 
            Je geeft je antwoord ALLEEN in JSON format zonder enige andere tekst.
            Zorg ervoor dat de JSON syntax volledig correct is."""),
            HumanMessage(content="""Analyseer het volgende transcript en identificeer ontbrekende informatie.
            
            Transcript: {transcript}
            
            GEEF JE ANTWOORD ALLEEN IN DIT JSON FORMAT:
            {
                "complete_info": {
                    "leningdeel": {},
                    "werkloosheid": {},
                    "aow": {}
                },
                "missing_info": {
                    "leningdeel": [],
                    "werkloosheid": [],
                    "aow": []
                },
                "next_question": "vraag hier",
                "context": "context hier"
            }""")
        ])
        
        # Conversation prompt template
        self.conversation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een vriendelijke hypotheekadviseur die ontbrekende informatie verzamelt.
            Je geeft je antwoord ALLEEN in JSON format zonder enige andere tekst.
            Zorg ervoor dat de JSON syntax volledig correct is."""),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(content="""
            Laatste antwoord klant: {user_response}
            
            Nog ontbrekende informatie: {missing_info}
            
            GEEF JE ANTWOORD ALLEEN IN DIT JSON FORMAT:
            {
                "next_question": "vraag hier",
                "context": "context hier",
                "processed_info": {},
                "remaining_missing_info": []
            }""")
        ])

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript and returns structured information."""
        try:
            # Get response from LLM
            messages = self.analysis_prompt.format_messages(transcript=transcript)
            response = self.llm.invoke(messages)
            
            # Extract content and parse JSON
            content = response.content
            logger.info(f"Raw LLM response: {content}")
            
            # Clean the response if needed
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("`"):
                content = content.strip("`")
            
            # Parse JSON
            result = json.loads(content)
            logger.info("Successfully analyzed transcript")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return DEFAULT_RESPONSE

    def process_user_response(
        self, 
        conversation_history: str, 
        user_response: str, 
        missing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Processes user response and returns next interaction details."""
        try:
            # Format conversation history into messages
            messages = [
                SystemMessage(content=line) if "AI: " in line 
                else HumanMessage(content=line.replace("Klant: ", ""))
                for line in conversation_history.split("\n")
                if line.strip()
            ]
            
            # Get response from LLM
            prompt_messages = self.conversation_prompt.format_messages(
                history=messages,
                user_response=user_response,
                missing_info=json.dumps(missing_info, ensure_ascii=False)
            )
            
            response = self.llm.invoke(prompt_messages)
            
            # Extract content and parse JSON
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("`"):
                content = content.strip("`")
            
            result = json.loads(content)
            logger.info("Successfully processed user response")
            return result
            
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {
                "next_question": "Kunt u dat nog eens anders formuleren?",
                "context": "Ik begreep uw antwoord niet helemaal.",
                "processed_info": {},
                "remaining_missing_info": missing_info
            }

    @staticmethod
    def format_conversation_history(messages: list) -> str:
        """Formats the conversation history into a string."""
        return "\n".join([
            f"{'AI: ' if msg['is_ai'] else 'Klant: '}{msg['content']}"
            for msg in messages
        ])