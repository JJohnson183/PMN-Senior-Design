#============================= Meeting ==============================#
# One meeting's info (None means not found yet)
class Meeting:
    # Store the meeting's info (location and time are often filled in later from its PDF)
    def __init__(self, title, date, pdf_links, location=None, time=None):
        self.title = title
        self.date = date
        self.pdf_links = pdf_links
        self.location = location
        self.time = time

    # True if the meeting has at least one PDF link
    def has_pdfs(self):
        return len(self.pdf_links) > 0
