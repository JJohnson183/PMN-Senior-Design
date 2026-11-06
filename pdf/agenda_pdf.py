import requests
import threading
import pypdfium2 as pdfium # Used for reading the text out of PDF files
from email.utils import parsedate_to_datetime
from pdf.header_rules import extract_meeting_info
from pdf.ai_extraction import extract_with_ai


pdfiumLock = threading.Lock()  # PDFium can't read PDFs on two threads at once

#============================= Agenda PDF ==============================#
# One agenda PDF online: when it was uploaded, its text, and the meeting info in it
class AgendaPdf:
    # Store the PDF's link (nothing is downloaded until a method needs it)
    def __init__(self, url):
        self.url = url

    # Upload date from the server's "Last-Modified" header, or None if the server doesn't say
    def upload_date(self):
        try:
            response = requests.head(self.url, timeout=10, allow_redirects=True)  # Headers only, no download
            uploaded = response.headers.get("Last-Modified")
            return parsedate_to_datetime(uploaded).date() if uploaded else None
        except (requests.RequestException, ValueError, TypeError):
            return None

    # Extract the text from the PDF file (None if it can't be downloaded or read)
    def text(self):
        try:
            # 1) Download the PDF into memory
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()

            # 2) Read the text from every page and join it into one string ("\f" marks each new page)
            with pdfiumLock, pdfium.PdfDocument(response.content) as document:
                text = "\f".join(page.get_textpage().get_text_bounded() for page in document)

            # 3) Use "\n" line endings, and remove the "\x02" PDFium puts where a word was hyphenated across two lines
            text = text.replace("\r\n", "\n").replace("\x02", "")

            # 4) Warn if no text was found since the PDF is likely a scanned image
            if not text.strip():
                print(f"No text found in {self.url}, it may be a scanned image")

            return text
        except Exception as e:
            print(f"Error extracting PDF {self.url}: {e}")
            return None

    # Date, location, start time and summary: the AI first, manual extraction as backup (None if the PDF can't be read)
    def meeting_info(self):
        # 1) Get the PDF's text and the manual extraction results
        text = self.text()
        if text is None:
            return None
        manual = extract_meeting_info(text)

        # 2) Extract information from the pdfs with AI
        ai = extract_with_ai(text, self.url)
        if ai is None:
            manual["summary"] = None
            return manual

        # 3) Use the AI results and the manual extraction results for empty or failed fields (failed ones are empty)
        info = {"date": ai["date"], "location": ai["location"], "time": ai["time"], "summary": ai["summary"]}
        for name in ("date", "location", "time"):
            if info[name] is None:
                info[name] = manual[name]
        return info
