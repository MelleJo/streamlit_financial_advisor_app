class AppState:
    def __init__(self):
        self.step = "input"  # Changed initial step to input
        self.transcript = None
        self.result = None
        self.conversation_history = []
        self.missing_info = None
        self.analysis_complete = False
        
    def add_message(self, content, is_ai=False):
        self.conversation_history.append({
            "content": content,
            "is_ai": is_ai
        })
    
    def set_transcript(self, transcript):
        self.transcript = transcript
    
    def set_missing_info(self, missing_info):
        self.missing_info = missing_info
    
    def set_result(self, result):
        self.result = result
    
    def set_step(self, step):
        self.step = step
    
    def set_analysis_complete(self, complete):
        self.analysis_complete = complete
    
    def reset(self):
        self.__init__()