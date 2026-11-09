def getMeeting():
    pass


def updateMeeting():
    pass


class Municipality:
    def __init__(self):
        self.name = ""
        self.sourceURL = ""
        self.municipalityID = 0

    def change_municipality_source(self, url):
        self.sourceURL = url


class Meeting(Municipality):
    def __init__(self):
        super().__init__()
        self.meetingID = 0
        self.date = 0
        self.title = ""
        self.location = ""
        self.committee = ""
        self.meetingURL = ""
        self.summary = ""
        self.municipality = Municipality

    def agenda_fetch(self):
        # this function will grab the pdf from the URL
        pass

    def process_agenda(self):
        # this funtion will process the grabbed agenda
        pass

    def fill_meeting_info(self):
        # this will fill out the class params to make them no longer default
        pass

    def summarize_agenda(self):
        # ship it to claude and save the result to summary
        pass

    def store_meeting(self):
        # send the data to the DB
        pass

    def create_meeting(self):
        self.agenda_fetch()
        self.process_agenda()
        self.fill_meeting_info()
        self.store_meeting()
        return True

