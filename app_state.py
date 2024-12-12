"""
File: app_state.py
Manages the application state for the Veldhuis Advies Assistant.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

@dataclass
class FPState:
    """State management for Financial Planning functionality"""
    samenvatting: Dict = field(default_factory=lambda: {
        "netto_besteedbaar_inkomen": None,
        "hoofdpunten": [],
        "kernadvies": None
    })
    
    uitwerking_advies: Dict = field(default_factory=lambda: {
        "content": None,
        "graphs": None
    })
    
    huidige_situatie: Dict = field(default_factory=lambda: {
        "content": None,
        "graphs": None
    })
    
    situatie_later: Dict = field(default_factory=lambda: {
        "voor_advies": None,
        "na_advies": None,
        "graphs": None
    })
    
    situatie_overlijden: Dict = field(default_factory=lambda: {
        "voor_advies": None,
        "na_advies": None,
        "graphs": None
    })
    
    situatie_arbeidsongeschiktheid: Dict = field(default_factory=lambda: {
        "voor_advies": None,
        "na_advies": None,
        "graphs": None
    })
    
    erven_schenken: Dict = field(default_factory=dict)
    
    actiepunten: Dict = field(default_factory=lambda: {
        "client": [],
        "veldhuis": []
    })
    
    sections_complete: Dict = field(default_factory=lambda: {
        "samenvatting": False,
        "uitwerking_advies": False,
        "huidige_situatie": False,
        "situatie_later": False,
        "situatie_overlijden": False,
        "situatie_arbeidsongeschiktheid": False,
        "erven_schenken": False,
        "actiepunten": False
    })

    def update_section(self, section: str, content: Dict) -> None:
        """Update content for a specific section"""
        if hasattr(self, section):
            setattr(self, section, content)
            self.sections_complete[section] = True

    def is_complete(self) -> bool:
        """Check if all sections are complete"""
        return all(self.sections_complete.values())

    def get_progress(self) -> float:
        """Get progress percentage"""
        completed = sum(1 for x in self.sections_complete.values() if x)
        total = len(self.sections_complete)
        return (completed / total) * 100 if total > 0 else 0

class AppState:
    """Main application state management"""
    def __init__(self):
        # Basic state
        self.step = "input"
        self.active_module = "hypotheek"  # Default module
        
        # Shared state
        self.transcript = None
        self.klantprofiel = None
        self.result = None
        self.additional_info = None
        self.conversation_history = []
        
        # Module-specific state
        self.missing_info = None
        self.analysis_complete = False
        self.structured_qa_history = []
        self.remaining_topics = {}
        
        # FP specific state
        self.fp_state = FPState()

    def set_klantprofiel(self, content: str) -> None:
        """Set the klantprofiel content."""
        self.klantprofiel = content

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
        """Set additional information gathered through questions."""
        self.additional_info = additional_info
        if 'conversation_history' in additional_info:
            self._update_structured_history(additional_info['conversation_history'])

    def _update_structured_history(self, conversation_history: List[str]) -> None:
        """Update structured Q&A history from conversation history."""
        current_qa = {}
        for message in conversation_history:
            if message.startswith("AI: "):
                current_qa['question'] = message[4:]
            elif message.startswith("Klant: "):
                current_qa['answer'] = message[7:]
                if 'question' in current_qa:
                    self.structured_qa_history.append(dict(current_qa))
                    current_qa = {}

    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the final analysis result."""
        self.result = result

    def set_step(self, step: str) -> None:
        """Set the current step in the application flow."""
        self.step = step

    def add_message(self, content: str, is_ai: bool = False, context: Optional[str] = None) -> None:
        """Add a message to the conversation history."""
        message = {
            "content": content,
            "is_ai": is_ai,
            "timestamp": None  # Could add timestamp if needed
        }
        if context:
            message["context"] = context
        
        self.conversation_history.append(message)

    def add_qa_pair(self, question: str, answer: str, context: str, category: str) -> None:
        """Add a structured Q&A pair with context and category."""
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
        """Get combined information from all sources."""
        return {
            "transcript": self.transcript,
            "klantprofiel": self.klantprofiel,
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

    def reset(self) -> None:
        """Reset the application state but keep active module."""
        current_module = self.active_module
        self.__init__()
        self.active_module = current_module
        self.step = "input"

    def switch_module(self, module: str) -> None:
        """Switch to a different module and reset appropriate state."""
        if module in ["hypotheek", "pensioen", "fp"]:
            # Save current module state if needed
            
            # Switch module
            self.active_module = module
            self.step = "input"
            
            # Clear module-specific state
            self.transcript = None
            self.result = None
            self.missing_info = None
            self.additional_info = None
            self.conversation_history = []
            self.structured_qa_history = []
            self.remaining_topics = {}
            
            # Reset FP state if switching to/from FP
            if module == "fp":
                self.fp_state = FPState()