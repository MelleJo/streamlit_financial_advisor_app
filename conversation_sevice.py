import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
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

            Zorg ervoor dat je output valide JSON is.
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

            Zorg ervoor dat je output valide JSON is.
            """
        )
        
        # Create chains using the new method
        self.analysis_chain = self.analysis_prompt | self.llm
        self.conversation_chain = self.conversation_prompt | self.llm

    def analyze_initial_transcript(self, transcript):
        try:
            # Use invoke instead of run
            result = self.analysis_chain.invoke({"transcript": transcript})
            
            # Extract content from the result
            content = result.content if hasattr(result, 'content') else str(result)
            
            # Ensure we're working with clean JSON string
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3]  # Remove JSON code block markers
            elif content.startswith("`"):
                content = content.strip("`")
                
            return json.loads(content)
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
            # Use invoke instead of run
            result = self.conversation_chain.invoke({
                "conversation_history": conversation_history,
                "user_response": user_response,
                "missing_info": json.dumps(missing_info, ensure_ascii=False)
            })
            
            # Extract content from the result
            content = result.content if hasattr(result, 'content') else str(result)
            
            # Clean up JSON string
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("`"):
                content = content.strip("`")
                
            return json.loads(content)
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