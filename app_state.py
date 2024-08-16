class AppState:
    def __init__(self):
        self.step = "choose_method"
        self.upload_method = None
        self.transcript = None
        self.result = None

    def set_step(self, step):
        self.step = step

    def set_upload_method(self, method):
        self.upload_method = method

    def set_transcript(self, transcript):
        self.transcript = transcript

    def set_result(self, result):
        self.result = result

    def reset(self):
        self.__init__()