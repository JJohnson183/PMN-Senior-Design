class Meeting:
    def __init__(self, title, date, pdf_links):
        self.title = title
        self.date = date
        self.pdf_links = pdf_links

    def has_pdfs(self):
        return len(self.pdf_links) > 0
