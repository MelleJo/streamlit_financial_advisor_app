import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.3,
            openai_api_key=api_key
        )
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

            Geef je antwoord in het volgende JSON-formaat:
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
            Geef je antwoord in JSON:
            {{
                "next_question": "volgende vraag",
                "context": "uitleg waarom deze vraag belangrijk is",
                "processed_info": {{}},
                "remaining_missing_info": []
            }}
            """
        )
        
        self.analysis_chain = LLMChain(llm=self.llm, prompt=self.analysis_prompt)
        self.conversation_chain = LLMChain(llm=self.llm, prompt=self.conversation_prompt)

    def analyze_initial_transcript(self, transcript):
        try:
            response = self.analysis_chain.run(transcript=transcript)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            return None

    def process_user_response(self, conversation_history, user_response, missing_info):
        try:
            response = self.conversation_chain.run(
                conversation_history=conversation_history,
                user_response=user_response,
                missing_info=json.dumps(missing_info, ensure_ascii=False)
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return None

    def format_conversation_history(self, messages):
        return "\n".join([
            f"{'AI: ' if msg['is_ai'] else 'Klant: '}{msg['content']}"
            for msg in messages
        ])