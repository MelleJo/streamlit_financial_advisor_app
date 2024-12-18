"""
File: fp_integration_service.py
Coordinates all Financial Planning components and handles the overall flow.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
from fp_analysis_service import FPAnalysisService
from fp_report_service import FPReportService
from fp_prompts import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FPState:
    """State management for FP analysis process."""
    transcript: Optional[str] = None
    klantprofiel: Optional[str] = None
    initial_analysis: Optional[Dict[str, Any]] = None
    missing_info: Optional[Dict[str, List[str]]] = None
    section_drafts: Optional[Dict[str, str]] = None
    final_report: Optional[Dict[str, Any]] = None
    graphs_required: Optional[Dict[str, List[Dict[str, Any]]]] = None
    qa_history: List[Dict[str, Any]] = None

class FPIntegrationService:
    def __init__(self, api_key: str):
        """Initialize all required services."""
        self.analysis_service = FPAnalysisService(api_key)
        self.report_service = FPReportService()
        self.state = FPState()
        self.api_key = api_key

    async def process_input(self, transcript: str, klantprofiel: str) -> Dict[str, Any]:
        """Process initial input and coordinate analysis."""
        try:
            # Store input
            self.state.transcript = transcript
            self.state.klantprofiel = klantprofiel
            
            # Perform initial analysis
            initial_result = await self.analysis_service.analyze_input(transcript, klantprofiel)
            self.state.initial_analysis = initial_result["analysis"]
            self.state.missing_info = initial_result["missing_info"]
            self.state.section_drafts = initial_result["section_drafts"]
            self.state.graphs_required = initial_result["graphs_needed"]
            
            return {
                "status": "success",
                "missing_info": self.state.missing_info,
                "next_questions": self._generate_follow_up_questions()
            }
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            return {
                "status": "error",
                "message": "Error processing input"
            }

    async def process_qa_response(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """Process a Q&A interaction and update analysis."""
        try:
            # Add to QA history
            qa_pair = {
                "question": question,
                "answer": answer,
                "context": context,
                "timestamp": None  # Could add timestamp if needed
            }
            if not self.state.qa_history:
                self.state.qa_history = []
            self.state.qa_history.append(qa_pair)
            
            # Update analysis with new information
            updated_analysis = await self._update_analysis_with_qa(qa_pair)
            
            # Check if we have all needed information
            is_complete = self._check_completion()
            
            return {
                "status": "success",
                "is_complete": is_complete,
                "next_questions": [] if is_complete else self._generate_follow_up_questions(),
                "updated_sections": updated_analysis.get("updated_sections", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing Q&A: {str(e)}")
            return {
                "status": "error",
                "message": "Error processing answer"
            }

    async def generate_final_report(self) -> Dict[str, Any]:
        """Generate the final report when all information is complete."""
        try:
            # Verify we have all needed information
            if not self._check_completion():
                return {
                    "status": "error",
                    "message": "Missing required information"
                }
            
            # Generate final report
            self.state.final_report = await self._generate_complete_report()
            
            return {
                "status": "success",
                "report": self.state.final_report
            }
            
        except Exception as e:
            logger.error(f"Error generating final report: {str(e)}")
            return {
                "status": "error",
                "message": "Error generating report"
            }

    def _check_completion(self) -> bool:
        """Check if we have all required information."""
        if not self.state.missing_info:
            return True
            
        return all(not items for items in self.state.missing_info.values())

    def _generate_follow_up_questions(self) -> List[Dict[str, Any]]:
        """Generate follow-up questions based on missing information."""
        questions = []
        
        if not self.state.missing_info:
            return questions
            
        for category, missing_items in self.state.missing_info.items():
            for item in missing_items:
                question = self._format_question_for_item(category, item)
                if question:
                    questions.append(question)
                    
        return questions

    def _format_question_for_item(self, category: str, item: str) -> Optional[Dict[str, Any]]:
        """Format a specific question for a missing item."""
        question_templates = {
            "nbi": {
                "inkomen": "Kunt u uw huidige netto maandinkomen specificeren?",
                "vaste_lasten": "Welke vaste lasten heeft u momenteel?",
                "gewenst_niveau": "Welk maandelijks besteedbaar inkomen wenst u?"
            },
            "pensioen": {
                "huidige_opbouw": "Hoeveel pensioen bouwt u momenteel op via uw werkgever?",
                "gewenst_inkomen": "Welk inkomen wenst u na pensionering?",
                "aow_leeftijd": "Weet u uw AOW-leeftijd?"
            },
            "risicos": {
                "overlijden": "Heeft u voorzieningen voor het geval van overlijden?",
                "ao": "Hoe bent u verzekerd tegen arbeidsongeschiktheid?",
                "werkloosheid": "Heeft u een buffer voor het geval van werkloosheid?"
            }
        }
        
        if category in question_templates and item in question_templates[category]:
            return {
                "question": question_templates[category][item],
                "context": f"Informatie nodig over {item} voor {category} analyse"
            }
        return None

    async def _update_analysis_with_qa(self, qa_pair: Dict[str, Any]) -> Dict[str, Any]:
        """Update analysis based on new Q&A information."""
        try:
            # Combine all information for reanalysis
            combined_text = f"{self.state.transcript}\n\nAanvullende informatie:\n"
            for qa in self.state.qa_history:
                combined_text += f"\nVraag: {qa['question']}\nAntwoord: {qa['answer']}\n"
            
            # Rerun analysis
            updated_result = await self.analysis_service.analyze_input(
                combined_text,
                self.state.klantprofiel
            )
            
            # Update state
            self.state.initial_analysis = updated_result["analysis"]
            self.state.missing_info = updated_result["missing_info"]
            self.state.section_drafts = updated_result["section_drafts"]
            
            return {
                "updated_sections": list(updated_result["section_drafts"].keys())
            }
            
        except Exception as e:
            logger.error(f"Error updating analysis with Q&A: {str(e)}")
            return {}

    async def _generate_complete_report(self) -> Dict[str, Any]:
        """Generate the complete final report."""
        try:
            # Combine all information
            all_info = {
                "transcript": self.state.transcript,
                "klantprofiel": self.state.klantprofiel,
                "analysis": self.state.initial_analysis,
                "qa_history": self.state.qa_history,
                "graphs_required": self.state.graphs_required
            }
            
            # Generate report using report service
            return await self.report_service.generate_report(all_info)
            
        except Exception as e:
            logger.error(f"Error generating complete report: {str(e)}")
            return {}