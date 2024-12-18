"""
File: conversation_service.py
Manages the conversational flow and analysis for the AI Hypotheek Assistent.
This service handles the interactive dialogue between the user and the AI advisor,
utilizing gpt-4o to:
1. Analyze transcripts to identify complete and missing information
2. Process user responses and determine appropriate follow-up questions
3. Maintain conversation context and history
The service ensures structured information gathering through JSON-formatted responses
and handles conversation state management for mortgage advice sessions.
"""

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
import logging
import json
from typing import Dict, Any
from checklist_analysis_service import ChecklistAnalysisService, CHECKLIST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4oo",
            temperature=0.3,
            api_key=st.secrets["OPENAI_API_KEY"]
        )
        self.checklist_service = ChecklistAnalysisService(api_key=api_key)
        
        # Analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""Je bent een hypotheekadviseur die transcripten analyseert. 
            Gebruik de checklist om te bepalen welke informatie ontbreekt.
            Je geeft je antwoord ALLEEN in JSON format zonder enige andere tekst.
            Zorg ervoor dat de JSON syntax volledig correct is."""),
            HumanMessage(content="""Analyseer het volgende transcript en identificeer ontbrekende informatie.
            
            Transcript: {transcript}
            
            Checklist van verplichte onderdelen:
            {checklist}
            
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
            Gebruik de checklist om gerichte vragen te stellen over ontbrekende informatie.
            Stel vragen die specifiek ingaan op de ontbrekende onderdelen.
            Je geeft je antwoord ALLEEN in JSON format zonder enige andere tekst.
            Zorg ervoor dat de JSON syntax volledig correct is."""),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(content="""
            Laatste antwoord klant: {user_response}
            
            Checklist van verplichte onderdelen:
            {checklist}
            
            Nog ontbrekende informatie volgens analyse: {missing_info}
            
            GEEF JE ANTWOORD ALLEEN IN DIT JSON FORMAT:
            {
                "next_question": "vraag hier",
                "context": "context hier",
                "processed_info": {},
                "remaining_missing_info": []
            }""")
        ])

    def analyze_initial_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes transcript and generates dynamic questions based on missing info."""
        try:
            messages = [
                SystemMessage(content="""Je bent een hypotheekadviseur die het gesprek analyseert.
                Op basis van de checklist en wat er ontbreekt in het transcript, genereer je een relevante 
                vraag om de belangrijkste ontbrekende informatie te verzamelen.
                
                Zorg dat je:
                1. De checklist gebruikt om ontbrekende informatie te identificeren
                2. De meest kritische ontbrekende informatie eerst vraagt
                3. De vraag natuurlijk en conversationeel formuleert
                4. Aansluit bij wat al wel bekend is uit het transcript"""),
                HumanMessage(content=f"""
                TRANSCRIPT:
                {transcript}
                
                CHECKLIST:
                {json.dumps(CHECKLIST, ensure_ascii=False)}
                
                Genereer een specifieke vraag voor de belangrijkste ontbrekende informatie.
                Geef je antwoord in dit format:
                {{
                    "next_question": "je vraag hier",
                    "context": "waarom je deze vraag stelt",
                    "missing_items": ["lijst", "van", "ontbrekende", "items"]
                }}
                """)
            ]

            # Use gpt-4oo-mini for question generation
            mini_llm = ChatOpenAI(
                model="gpt-4oo-mini",
                temperature=0.3,
                openai_api_key=self.api_key
            )
            
            response = mini_llm.invoke(messages)
            content = response.content.strip()
            
            # Process response
            try:
                result = json.loads(content)
                logger.info(f"Generated question: {result['next_question']}")
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                return {
                    "next_question": "Wat is het gewenste hypotheekbedrag?",
                    "context": "Basis informatie nodig voor hypotheekadvies",
                    "missing_items": ["hypotheekbedrag"]
                }
                
        except Exception as e:
            logger.error(f"Error in initial analysis: {str(e)}")
            return {
                "next_question": "Wat is het gewenste hypotheekbedrag?",
                "context": "Basis informatie nodig voor hypotheekadvies",
                "missing_items": ["hypotheekbedrag"]
            }

    def process_user_response(
    self, 
    conversation_history: str, 
    user_response: str, 
    missing_info: Dict[str, list]
) -> Dict[str, Any]:
        """Processes user response and generates next question based on remaining missing info."""
        try:
            messages = [
                SystemMessage(content="""Je bent een hypotheekadviseur in gesprek met een klant.
                Analyseer het antwoord en bepaal de volgende vraag op basis van nog ontbrekende informatie.
                
                Zorg dat je:
                1. Het antwoord verwerkt in je begrip van de situatie
                2. Kijkt welke informatie nog ontbreekt
                3. Een logische vervolgvraag stelt
                4. De vraag natuurlijk en conversationeel formuleert"""),
                HumanMessage(content=f"""
                CONVERSATIE TOT NU TOE:
                {conversation_history}
                
                LAATSTE ANTWOORD KLANT:
                {user_response}
                
                NOG ONTBREKENDE INFORMATIE:
                {json.dumps(missing_info, ensure_ascii=False)}
                
                Bepaal de volgende vraag. Geef je antwoord in dit format:
                {{
                    "next_question": "je vraag hier",
                    "context": "waarom je deze vraag stelt",
                    "processed_info": {{"categorie": "verwerkte informatie"}},
                    "remaining_missing_info": ["nog ontbrekende items"]
                }}
                """)
            ]

            # Use gpt-4oo-mini for dynamic question generation
            mini_llm = ChatOpenAI(
                model="gpt-4oo-mini",
                temperature=0.3,
                openai_api_key=self.api_key
            )
            
            response = mini_llm.invoke(messages)
            content = response.content.strip()
            
            # Process response
            try:
                result = json.loads(content)
                logger.info(f"Generated follow-up question: {result['next_question']}")
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                return self._get_default_question_response()
                
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return self._get_default_question_response()
        
    def _get_default_question_response(self) -> Dict[str, Any]:
        """Returns a default question response if processing fails."""
        return {
            "next_question": "Kunt u meer vertellen over uw inkomenssituatie?",
            "context": "We hebben meer informatie nodig over uw financiële situatie",
            "processed_info": {},
            "remaining_missing_info": ["inkomen"]
        }

    def _generate_question_for_missing_topic(self, category: str, missing_item: str) -> str:
        """Generates a specific question based on the missing checklist item."""
        # First check if the category exists in CHECKLIST
        if category not in CHECKLIST:
            return f"Kun je meer vertellen over {missing_item.lower()}?"
            
        questions = {
            "leningdeel": {
                "Exacte leningbedrag met onderbouwing": "Wat is het exacte leningbedrag dat je nodig hebt en waarom?",
                "NHG keuze en onderbouwing": "Heb je al nagedacht over Nationale Hypotheek Garantie (NHG)?",
                "Maandlasten berekening": "Welke maandlasten heb je voor ogen?",
                "Rentevaste periode met motivatie": "Welke rentevaste periode heeft je voorkeur en waarom?",
                "Hypotheekvorm met toelichting": "Welke hypotheekvorm spreekt je het meeste aan?",
                "Fiscale aspecten en voordelen": "Ben je bekend met de fiscale voordelen van verschillende hypotheekvormen?"
            },
            "werkloosheid": {
                "Huidige arbeidssituatie": "Kun je je huidige arbeidssituatie toelichten?",
                "Werkloosheidsrisico analyse": "Hoe schat je het risico op werkloosheid in je sector in?",
                "WW-uitkering en duur": "Weet je wat je WW-rechten zijn?",
                "Impact op maandlasten": "Hoe zou werkloosheid je hypotheeklasten beïnvloeden?",
                "Verzekeringswensen en dekking": "Heb je gedacht aan een werkloosheidsverzekering?"
            },
            "aow": {
                "AOW-leeftijd en planning": "Weet je wanneer je AOW gaat ontvangen?",
                "Hypotheeksituatie bij pensionering": "Hoe zie je je hypotheek voor je als je met pensioen gaat?",
                "Pensioeninkomen en opbouw": "Hoe bouw je pensioen op?",
                "Toekomstperspectief na AOW": "Wat zijn je plannen voor na je pensionering?",
                "Vermogensplanning": "Heb je al nagedacht over vermogensopbouw voor later?"
            }
        }
        
        return questions.get(category, {}).get(
            missing_item, 
            f"Kun je meer vertellen over {missing_item.lower()}?"
        )

    @staticmethod
    def format_conversation_history(messages: list) -> str:
        """Formats the conversation history into a string."""
        return "\n".join([
            f"{'AI: ' if msg['is_ai'] else 'Klant: '}{msg['content']}"
            for msg in messages
        ])
