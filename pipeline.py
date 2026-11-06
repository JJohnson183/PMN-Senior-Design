from fetchers.civicclerk import CivicClerkFetcher
from fetchers.html_page import HtmlPageFetcher
from pdf.agenda_pdf import AgendaPdf
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor


civicClerkCheck = "civicclerk.com"  # Check if the URL is from CivicClerk
maxDaysAhead = 365  # Dates further out than this are typos (e.g. "2108" for "2018"), not real meetings
uploadWindowDays = 30  # Undated PDFs uploaded longer ago than this are too old to be an upcoming agenda

#============================= Core Flow ====================================#
# Pick the kind of fetcher a site needs from its URL (a plain web page unless it's CivicClerk)
def pick_fetcher(url):
    if civicClerkCheck in url:
        return CivicClerkFetcher()
    return HtmlPageFetcher()

# True if the date is from today to maxDaysAhead out
def in_date_range(day, today):
    return today <= day <= today + timedelta(days=maxDaysAhead)

# Fill a meeting's missing date, location, time and summary from its first PDF (True if the PDF was read)
def fill_missing_info(meeting):
    # 1) Skip meetings with no PDF or nothing missing
    if not meeting.has_pdfs() or None not in (meeting.date, meeting.location, meeting.time, meeting.summary):
        return False

    # 2) Undated: skip files uploaded too long ago to be an upcoming agenda (read it if the server doesn't say)
    pdf = AgendaPdf(meeting.pdf_links[0])
    if meeting.date is None:
        uploaded = pdf.upload_date()
        if uploaded and uploaded < date.today() - timedelta(days=uploadWindowDays):
            return False

    # 3) Read the PDF and fill only the empty fields
    info = pdf.meeting_info()
    if info is None:
        return False
    meeting.date = meeting.date or info["date"]
    meeting.location = meeting.location or info["location"]
    meeting.time = meeting.time or info["time"]
    meeting.summary = meeting.summary or info["summary"]
    return True

# Fetch a site's meetings, fill missing info from their PDFs, and keep only upcoming ones
def get_meetings(url):
    # 1) Pick the fetcher (CivicClerk or HTML) and fetch the meetings
    meetings = pick_fetcher(url).fetch(url)
    if not meetings:
        return meetings
    fetched = len(meetings)

    # 2) Drop meetings dated outside today to a year ahead (undated ones may get a date from their PDF)
    today = date.today()
    meetings = [meeting for meeting in meetings if meeting.date is None or in_date_range(meeting.date, today)]

    # 3) Fill missing info from each meeting's PDF (10 at a time to keep it fast)
    with ThreadPoolExecutor(max_workers=10) as pool:
        read = sum(pool.map(fill_missing_info, meetings))

    # 4) Drop meetings still undated, or whose PDF date is out of range
    upcoming = [meeting for meeting in meetings if meeting.date is not None and in_date_range(meeting.date, today)]
    print(f"Read {read} PDFs, kept {len(upcoming)} of {fetched} meetings (dropped past, undated, or over a year ahead)")
    return upcoming
