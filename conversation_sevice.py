import streamlit as st
from langchain_community.chat_models import ChatOpenAI  # Updated import
from langchain_core.prompts import PromptTemplate  # Updated import
from langchain_core.output_parsers import JsonOutputParser
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Updated parameter name
            temperature=0.3,
            openai_api_key=api_key
        )
        
        # Add JSON output parser
        self.json_parser = JsonOutputParser()
        
        # Analysis prompt
        self.analysis_prompt = PromptTemplate(
            input_variables=["transcript"],
            template="""
            Analyseer het volgende transcript van een hypotheekgesprek en identificeer ontbrekende informatie 
            voor de volgende categorieën:

            1. Leningdeel (bedrag, NHG, aflosvorm, looptijd, rentevaste periode)
            2. Werkloosheidsrisico (behoefte aan verzekering, gewenste dekking)
            3. AOW-planning (pensioendatum, gewenste situatie)

            Transcript:
            {transcript}

            Retourneer je antwoord in het volgende JSON-formaat:
            {{
                "complete_info": {{
                    "leningdeel": {{}},
                    "werkloosheid": {{}},
                    "aow": {{}}
                }},
                "missing_info": {{
                    "leningdeel": [],
                    "werkloosheid": [],
                    "aow": []
                }},
                "next_question": "eerste vraag die gesteld moet worden",
                "context": "uitleg waarom deze vraag belangrijk is"
            }}
            """
        )
        
        # Conversation prompt
        self.conversation_prompt = PromptTemplate(
            input_variables=["conversation_history", "user_response", "missing_info"],
            template="""
            Je bent een vriendelijke hypotheekadviseur die ontbrekende informatie verzamelt.

            Gespreksgeschiedenis:
            {conversation_history}

            Laatste antwoord klant:
            {user_response}

            Nog ontbrekende informatie:
            {missing_info}

            Bepaal de volgende vraag op basis van het antwoord en de nog ontbrekende informatie.
            Retourneer je antwoord in het volgende JSON-formaat:
            {{
                "next_question": "volgende vraag",
                "context": "uitleg waarom deze vraag belangrijk is",
                "processed_info": {{}},
                "remaining_missing_info": []
            }}
            """
        )
        
        # Create modern chain configurations using pipe syntax
        self.analysis_chain = (
            {"transcript": lambda x: x}
            | self.analysis_prompt 
            | self.llm
            | self.json_parser
        )

        self.conversation_chain = (
            {
                "conversation_history": lambda x: x["conversation_history"],
                "user_response": lambda x: x["user_response"],
                "missing_info": lambda x: x["missing_info"]
            }
            | self.conversation_prompt 
            | self.llm
            | self.json_parser
        )

    def analyze_initial_transcript(self, transcript):
        try:
            return self.analysis_chain.invoke(transcript)
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return {
                "complete_info": {"leningdeel": {}, "werkloosheid": {}, "aow": {}},
                "missing_info": {
                    "leningdeel": ["Basisinformatie ontbreekt"],
                    "werkloosheid": ["Basisinformatie ontbreekt"],
                    "aow": ["Basisinformatie ontbreekt"]
                },
                "next_question": "Kunt u mij vertellen wat het gewenste leningbedrag is?",
                "context": "We beginnen met de basisinformatie voor uw hypotheekaanvraag."
            }

    def process_user_response(self, conversation_history, user_response, missing_info):
        try:
            return self.conversation_chain.invoke({
                "conversation_history": conversation_history,
                "user_response": user_response,
                "missing_info": json.dumps(missing_info, ensure_ascii=False)
            })
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {
                "next_question": "Kunt u dat nog eens anders formuleren?",
                "context": "Ik begreep uw antwoord niet helemaal.",
                "processed_info": {},
                "remaining_missing_info": missing_info
            }

    def format_conversation_history(self, messages):
        return "\n".join([
            f"{'AI: ' if msg['is_ai'] else 'Klant: '}{msg['content']}"
            for msg in messages
        ])