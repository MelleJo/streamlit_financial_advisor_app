class AppState:
    def __init__(self):
        self.step = "select_persons"  # Changed initial step
        self.upload_method = None
        self.transcript = None
        self.result = None
        self.number_of_persons = None
        self.person_details = {}

    def set_number_of_persons(self, number):
        self.number_of_persons = number
        self.person_details = {f"person_{i+1}": {} for i in range(number)}

    def set_person_detail(self, person_id, key, value):
        if person_id in self.person_details:
            self.person_details[person_id][key] = value

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