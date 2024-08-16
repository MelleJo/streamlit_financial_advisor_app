class AppState:
    def __init__(self):
        self.step = "choose_method"
        self.user_input = None
        self.processing_result = None

    def set_step(self, step):
        self.step = step

    def set_user_input(self, user_input):
        self.user_input = user_input

    def set_processing_result(self, result):
        self.processing_result = result

    def reset(self):
        self.__init__()