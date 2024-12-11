"""
File: conversation_service.py
Manages the conversational flow and analysis for the AI Hypotheek Assistent.
This service handles the interactive dialogue between the user and the AI advisor,
utilizing GPT-4 to:
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
            model="gpt-4o-2024-08-06",
            temperature=0.3,
            openai_api_key=api_key
        )
        self.checklist_service = ChecklistAnalysisService(api_key)
        
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
        """Analyzes the initial transcript and returns structured information."""
        try:
            # First use checklist service to analyze gaps
            checklist_analysis = self.checklist_service.analyze_transcript(transcript)
            
            # Get response from LLM with checklist context
            messages = self.analysis_prompt.format_messages(
                transcript=transcript,
                checklist=json.dumps(CHECKLIST, ensure_ascii=False)
            )
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
            
            # Integrate checklist analysis results
            result["missing_info"] = checklist_analysis["missing_topics"]
            
            # Generate specific question based on missing topics
            if checklist_analysis["missing_topics"]:
                first_category = next(iter(checklist_analysis["missing_topics"]))
                first_missing = checklist_analysis["missing_topics"][first_category][0]
                result["next_question"] = self._generate_question_for_missing_topic(first_category, first_missing)
                result["context"] = f"We hebben meer informatie nodig over {CHECKLIST[first_category]['title'].lower()}"
            
            logger.info("Successfully analyzed transcript")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return {
                "complete_info": {"leningdeel": {}, "werkloosheid": {}, "aow": {}},
                "missing_info": checklist_analysis["missing_topics"] if 'checklist_analysis' in locals() else CHECKLIST,
                "next_question": "Kunt u mij vertellen wat het gewenste leningbedrag is?",
                "context": "We beginnen met de basisinformatie voor uw hypotheekaanvraag."
            }

    def process_user_response(
        self, 
        conversation_history: str, 
        user_response: str, 
        missing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Processes user response and returns next interaction details."""
        try:
            # Format conversation history into messages
            messages = []
            for line in conversation_history.split("\n"):
                if line.strip():
                    if line.startswith("AI: "):
                        messages.append(SystemMessage(content=line[4:]))
                    elif line.startswith("Klant: "):
                        messages.append(HumanMessage(content=line[7:]))
            
            # Get response from LLM with checklist context
            prompt_messages = self.conversation_prompt.format_messages(
                history=messages,
                user_response=user_response,
                checklist=json.dumps(CHECKLIST, ensure_ascii=False),
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
            logger.info(f"Processed user response: {result}")
            
            # Handle remaining_missing_info based on its type
            if "remaining_missing_info" in result:
                remaining_info = result["remaining_missing_info"]
                
                if isinstance(remaining_info, list):
                    # If it's a list, generate a question for the first missing item
                    if remaining_info:
                        first_missing = remaining_info[0]
                        result["next_question"] = f"Kunt u meer vertellen over {first_missing.lower()}?"
                        result["context"] = "We hebben aanvullende informatie nodig"
                else:
                    # If it's a dictionary, use the existing category-based logic
                    for category, items in remaining_info.items():
                        if items and isinstance(items, list) and items:
                            first_missing = items[0]
                            if category in CHECKLIST:
                                result["next_question"] = self._generate_question_for_missing_topic(category, first_missing)
                                result["context"] = f"We hebben meer informatie nodig over {CHECKLIST[category]['title'].lower()}"
                            break

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

    def _generate_question_for_missing_topic(self, category: str, missing_item: str) -> str:
        """Generates a specific question based on the missing checklist item."""
        # First check if the category exists in CHECKLIST
        if category not in CHECKLIST:
            return f"Kunt u meer vertellen over {missing_item.lower()}?"
            
        questions = {
            "leningdeel": {
                "Exacte leningbedrag met onderbouwing": "Wat is het exacte leningbedrag dat u nodig heeft en waarom?",
                "NHG keuze en onderbouwing": "Heeft u al nagedacht over Nationale Hypotheek Garantie (NHG)?",
                "Maandlasten berekening": "Welke maandlasten heeft u voor ogen?",
                "Rentevaste periode met motivatie": "Welke rentevaste periode heeft uw voorkeur en waarom?",
                "Hypotheekvorm met toelichting": "Welke hypotheekvorm spreekt u het meeste aan?",
                "Fiscale aspecten en voordelen": "Bent u bekend met de fiscale voordelen van verschillende hypotheekvormen?"
            },
            "werkloosheid": {
                "Huidige arbeidssituatie": "Kunt u uw huidige arbeidssituatie toelichten?",
                "Werkloosheidsrisico analyse": "Hoe schat u het risico op werkloosheid in uw sector in?",
                "WW-uitkering en duur": "Weet u wat uw WW-rechten zijn?",
                "Impact op maandlasten": "Hoe zou werkloosheid uw hypotheeklasten beïnvloeden?",
                "Verzekeringswensen en dekking": "Heeft u gedacht aan een werkloosheidsverzekering?"
            },
            "aow": {
                "AOW-leeftijd en planning": "Weet u wanneer u AOW gaat ontvangen?",
                "Hypotheeksituatie bij pensionering": "Hoe ziet u uw hypotheek voor zich als u met pensioen gaat?",
                "Pensioeninkomen en opbouw": "Hoe bouwt u pensioen op?",
                "Toekomstperspectief na AOW": "Wat zijn uw plannen voor na uw pensionering?",
                "Vermogensplanning": "Heeft u al nagedacht over vermogensopbouw voor later?"
            }
        }
        
        return questions.get(category, {}).get(
            missing_item, 
            f"Kunt u meer vertellen over {missing_item.lower()}?"
        )

    @staticmethod
    def format_conversation_history(messages: list) -> str:
        """Formats the conversation history into a string."""
        return "\n".join([
            f"{'AI: ' if msg['is_ai'] else 'Klant: '}{msg['content']}"
            for msg in messages
        ])
