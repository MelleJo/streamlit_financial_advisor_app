"""
File: checklist_analysis_service.py
Handles intelligent checklist-based analysis and question generation.
"""

import logging
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECKLIST_SECTIONS = {
    "leningdeel": [
        "Leningbedrag en dekking (NHG)",
        "Aflosvorm en looptijd",
        "Rentevaste periode en motivatie",
        "Fiscaal aspect (hypotheekrenteaftrek)",
        "Voorkeuren van de klant",
        "Aanvullende aanbevelingen"
    ],
    "werkloosheid": [
        "Doelstelling bij werkloosheid",
        "Toetslast en verantwoorde maandlasten",
        "Maximaal te verzekeren bedrag",
        "Reactie van de klant op het advies"
    ],
    "aow": [
        "Doelstelling vanaf AOW-datum",
        "Status van hypotheekaflossing op AOW-datum",
        "Financiële voordelen na AOW",
        "Toekomstperspectief na pensionering",
        "Aanvullende aanbevelingen voor na pensionering"
    ]
}

class ChecklistAnalysisService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            openai_api_key=api_key
        )
        
        # Analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Je bent een hypotheekadviseur die transcripten analyseert op basis van een checklist.
            Bepaal voor elk punt op de checklist of het voldoende behandeld is in het transcript.
            Geef je antwoord ALLEEN in het gevraagde JSON format."""),
            ("user", """
            Analyseer dit transcript en bepaal welke checklistpunten nog niet voldoende zijn behandeld:
            
            TRANSCRIPT:
            {transcript}
            
            CHECKLIST SECTIES:
            {checklist_sections}
            
            Geef je antwoord in dit JSON format:
            {{
                "missing_points": {{
                    "leningdeel": ["punt1", "punt2"],
                    "werkloosheid": ["punt3"],
                    "aow": ["punt4", "punt5"]
                }},
                "next_questions": [
                    {{
                        "question": "specifieke vraag hier",
                        "context": "waarom deze vraag belangrijk is",
                        "related_points": ["punt1", "punt4"]
                    }}
                ]
            }}""")
        ])
        
        # Question generation prompt
        self.question_prompt = ChatPromptTemplate.from_messages([
            ("system", """Je bent een hypotheekadviseur die gerichte vragen stelt om ontbrekende informatie te verzamelen.
            Focus op het stellen van duidelijke, specifieke vragen die helpen bij het invullen van ontbrekende checklistpunten."""),
            ("user", """
            ONTBREKENDE PUNTEN:
            {missing_points}
            
            EERDERE ANTWOORDEN:
            {previous_answers}
            
            Genereer de volgende vraag in dit JSON format:
            {{
                "question": "vraag hier",
                "context": "waarom deze vraag",
                "related_points": ["punt1", "punt2"]
            }}""")
        ])

    async def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyzes the transcript against the checklist."""
        try:
            response = await self.analysis_prompt.ainvoke({
                "transcript": transcript,
                "checklist_sections": json.dumps(CHECKLIST_SECTIONS, ensure_ascii=False)
            })
            
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Error in checklist analysis: {e}")
            return {
                "missing_points": CHECKLIST_SECTIONS,
                "next_questions": [{
                    "question": "Kunt u het gewenste leningbedrag bevestigen?",
                    "context": "We beginnen met de basisinformatie",
                    "related_points": ["Leningbedrag en dekking (NHG)"]
                }]
            }

    async def generate_next_question(
        self,
        missing_points: Dict[str, List[str]],
        previous_answers: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Generates the next most relevant question based on missing points."""
        try:
            response = await self.question_prompt.ainvoke({
                "missing_points": json.dumps(missing_points, ensure_ascii=False),
                "previous_answers": json.dumps(previous_answers, ensure_ascii=False)
            })
            
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return {
                "question": "Kunt u meer vertellen over uw situatie?",
                "context": "We hebben meer informatie nodig",
                "related_points": []
            }