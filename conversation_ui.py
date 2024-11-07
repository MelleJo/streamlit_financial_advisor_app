import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
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
        
        # Initialize output parser
        self.output_parser = JsonOutputParser()
        
        # Analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", "Je bent een hypotheekadviseur die transcripten analyseert. Geef je antwoord altijd in JSON format."),
            ("user", """
            Analyseer het volgende transcript en identificeer ontbrekende informatie:

            Transcript: {transcript}

            Geef je antwoord in exact dit JSON format:
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
            }
            """)
        ])
        
        # Conversation prompt template
        self.conversation_prompt = ChatPromptTemplate.from_messages([
            ("system", "Je bent een vriendelijke hypotheekadviseur die ontbrekende informatie verzamelt."),
            ("user", """
            Gespreksgeschiedenis:
            {conversation_history}

            Laatste antwoord klant:
            {user_response}

            Nog ontbrekende informatie:
            {missing_info}

            Geef je antwoord in exact dit JSON format:
            {
                "next_question": "vraag hier",
                "context": "context hier",
                "processed_info": {},
                "remaining_missing_info": []
            }
            """)
        ])

        # Create chains using modern syntax
        self.analysis_chain = self.analysis_prompt | self.llm | self.output_parser
        self.conversation_chain = self.conversation_prompt | self.llm | self.output_parser

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the initial transcript and returns structured information."""
        try:
            response = self.analysis_chain.invoke({"transcript": transcript})
            logger.info("Successfully analyzed transcript")
            return response
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
            response = self.conversation_chain.invoke({
                "conversation_history": conversation_history,
                "user_response": user_response,
                "missing_info": json.dumps(missing_info, ensure_ascii=False)
            })
            logger.info("Successfully processed user response")
            return response
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