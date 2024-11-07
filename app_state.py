from typing import Dict, Any, Optional

class AppState:
    def __init__(self):
        self.step = "input"
        self.transcript = None
        self.result = None
        self.missing_info = None
        self.additional_info = None
        self.conversation_history = []
        self.analysis_complete = False

    def set_transcript(self, transcript: str) -> None:
        """Set the initial transcript."""
        self.transcript = transcript

    def set_missing_info(self, missing_info: Dict[str, Any]) -> None:
        """Set information that's missing from the initial analysis."""
        self.missing_info = missing_info

    def set_additional_info(self, additional_info: Dict[int, Dict[str, str]]) -> None:
        """Set additional information gathered through questions."""
        self.additional_info = additional_info

    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the final analysis result."""
        self.result = result

    def set_step(self, step: str) -> None:
        """Set the current step in the application flow."""
        self.step = step

    def add_message(self, content: str, is_ai: bool = False) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "content": content,
            "is_ai": is_ai
        })

    def set_analysis_complete(self, complete: bool) -> None:
        """Set whether the analysis is complete."""
        self.analysis_complete = complete

    def get_combined_info(self) -> Dict[str, Any]:
        """Get combined information from all sources."""
        return {
            "transcript": self.transcript,
            "additional_info": self.additional_info,
            "missing_info": self.missing_info,
            "conversation_history": self.conversation_history
        }

    def reset(self) -> None:
        """Reset the application state."""
        self.__init__()