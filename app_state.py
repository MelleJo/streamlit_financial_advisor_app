"""
File: app_state.py
Manages the application state for the AI Hypotheek Assistent.
This class handles all state management including the current step in the application flow,
transcript data, analysis results, missing information, and conversation history.
It provides methods to modify and retrieve state data in a controlled manner.
"""

from typing import Dict, Any, Optional, List

class AppState:
    def __init__(self):
        # Existing state
        self.step = "input"
        self.transcript = None
        self.klantprofiel = None
        self.result = None
        self.missing_info = None
        self.additional_info = None
        self.conversation_history = []
        self.analysis_complete = False
        self.structured_qa_history = []
        self.remaining_topics = {}
        
        # New FP-specific state
        self.fp_report = {
            "samenvatting": None,
            "uitwerking_advies": None,
            "bevindingen_huidige_situatie": None,
            "situatie_voor_advies": None,
            "situatie_na_advies": None,
            "financiele_situatie_later": {
                "voor_advies": None,
                "na_advies": None
            },
            "financiele_situatie_overlijden": {
                "voor_advies": None,
                "na_advies": None
            },
            "financiele_situatie_arbeidsongeschiktheid": {
                "voor_advies": None,
                "na_advies": None
            },
            "erven_en_schenken": None,
            "actiepunten": {
                "client": [],
                "veldhuis": []
            }
        }
        
        # Track report sections completion
        self.fp_sections_complete = {
            "samenvatting": False,
            "uitwerking_advies": False,
            "bevindingen_huidige_situatie": False,
            "financiele_situatie_later": False,
            "financiele_situatie_overlijden": False,
            "financiele_situatie_arbeidsongeschiktheid": False,
            "erven_en_schenken": False,
            "actiepunten": False
        }

    def update_fp_section(self, section: str, content: dict) -> None:
        """Update a specific section of the FP report"""
        if section in self.fp_report:
            self.fp_report[section] = content
            self.fp_sections_complete[section] = True

    def get_fp_report_status(self) -> dict:
        """Get the completion status of the FP report"""
        return {
            "sections_complete": self.fp_sections_complete,
            "all_complete": all(self.fp_sections_complete.values())
        }

    def reset_fp_report(self) -> None:
        """Reset the FP report state"""
        self.__init__()

    def set_klantprofiel(self, content: str) -> None:
        """Set the klantprofiel content."""
        self.klantprofiel = content

    def get_combined_info(self) -> Dict[str, Any]:
        """Get combined information from all sources."""
        return {
            "transcript": self.transcript,
            "klantprofiel": self.klantprofiel,  # Include klantprofiel in combined info
            "additional_info": self.additional_info,
            "missing_info": self.missing_info,
            "conversation_history": self.conversation_history,
            "structured_qa_history": self.structured_qa_history,
            "remaining_topics": self.remaining_topics
        }
    
    def get_conversation_summary(self) -> str:
        """Get a formatted summary of the conversation history."""
        summary_parts = []
        
        if self.klantprofiel:
            summary_parts.append("Klantprofiel:\n" + self.klantprofiel)
            
        if self.transcript:
            summary_parts.append("\nOorspronkelijk transcript:\n" + self.transcript)
        
        if self.structured_qa_history:
            summary_parts.append("\nAanvullende vragen en antwoorden:")
            for qa in self.structured_qa_history:
                summary_parts.append(f"\nContext: {qa['context']}")
                summary_parts.append(f"Vraag: {qa['question']}")
                summary_parts.append(f"Antwoord: {qa['answer']}")
        
        return "\n".join(summary_parts)
    
    def set_transcript(self, transcript: str) -> None:
        """Set the initial transcript."""
        self.transcript = transcript

    def set_missing_info(self, missing_info: Dict[str, Any]) -> None:
        """Set information that's missing from the initial analysis."""
        self.missing_info = missing_info
        # Initialize remaining topics with missing info
        self.remaining_topics = {
            category: list(topics) for category, topics in missing_info.items()
            if topics
        }

    def set_additional_info(self, additional_info: Dict[str, Any]) -> None:
        """
        Set additional information gathered through questions.
        Now handles structured Q&A history.
        """
        self.additional_info = additional_info
        
        # If additional info contains conversation history, update structured history
        if 'conversation_history' in additional_info:
            self._update_structured_history(additional_info['conversation_history'])

    def _update_structured_history(self, conversation_history: List[str]) -> None:
        """Update structured Q&A history from conversation history."""
        current_qa = {}
        for message in conversation_history:
            if message.startswith("AI: "):
                current_qa['question'] = message[4:]  # Remove "AI: " prefix
            elif message.startswith("Klant: "):
                current_qa['answer'] = message[7:]  # Remove "Klant: " prefix
                if 'question' in current_qa:  # Only add if we have both Q&A
                    self.structured_qa_history.append(dict(current_qa))
                    current_qa = {}

    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the final analysis result."""
        self.result = result

    def set_step(self, step: str) -> None:
        """Set the current step in the application flow."""
        self.step = step

    def add_message(self, content: str, is_ai: bool = False, context: Optional[str] = None) -> None:
        """
        Add a message to the conversation history.
        Now includes context for better conversation tracking.
        """
        message = {
            "content": content,
            "is_ai": is_ai,
            "timestamp": None  # Could add timestamp if needed
        }
        if context:
            message["context"] = context
        
        self.conversation_history.append(message)

    def add_qa_pair(self, question: str, answer: str, context: str, category: str) -> None:
        """
        Add a structured Q&A pair with context and category.
        Also updates remaining topics.
        """
        qa_pair = {
            "question": question,
            "answer": answer,
            "context": context,
            "category": category
        }
        self.structured_qa_history.append(qa_pair)
        
        # Update conversation history as well
        self.add_message(question, is_ai=True, context=context)
        self.add_message(answer, is_ai=False)

    def update_remaining_topics(self, category: str, completed_topic: str) -> None:
        """Update the list of remaining topics after a topic is covered."""
        if category in self.remaining_topics:
            if completed_topic in self.remaining_topics[category]:
                self.remaining_topics[category].remove(completed_topic)
            if not self.remaining_topics[category]:
                del self.remaining_topics[category]

    def set_analysis_complete(self, complete: bool) -> None:
        """Set whether the analysis is complete."""
        self.analysis_complete = complete

    def get_combined_info(self) -> Dict[str, Any]:
        """
        Get combined information from all sources.
        Now includes structured Q&A history and remaining topics.
        """
        return {
            "transcript": self.transcript,
            "additional_info": self.additional_info,
            "missing_info": self.missing_info,
            "conversation_history": self.conversation_history,
            "structured_qa_history": self.structured_qa_history,
            "remaining_topics": self.remaining_topics
        }

    def get_conversation_summary(self) -> str:
        """
        Get a formatted summary of the conversation history.
        Useful for GPT context.
        """
        summary_parts = []
        
        if self.transcript:
            summary_parts.append("Oorspronkelijk transcript:\n" + self.transcript)
        
        if self.structured_qa_history:
            summary_parts.append("\nAanvullende vragen en antwoorden:")
            for qa in self.structured_qa_history:
                summary_parts.append(f"\nContext: {qa['context']}")
                summary_parts.append(f"Vraag: {qa['question']}")
                summary_parts.append(f"Antwoord: {qa['answer']}")
        
        return "\n".join(summary_parts)

    def reset(self) -> None:
        """Reset the application state."""
        self.__init__()
