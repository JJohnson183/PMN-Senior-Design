import requests
from bs4 import BeautifulSoup # Used for parsing HTML content for extracting links
from urllib.parse import urljoin, urlparse
from datetime import date, datetime

testUrl = "https://www.oshtemo.org/Boards-Committees/Township-Board/Township-Board-Agenda-Packets"


# https://kalamazoomi.portal.civicclerk.com
# https://kalamazoocomi.portal.civicclerk.com

# https://www.ktwp.org/board-of-trustees-meetings/  (Also has multiple other urls)

# https://www.oshtemo.org/Boards-Committees/Township-Board/Township-Board-Agenda-Packets
# https://www.oshtemo.org/Boards-Committees/Planning-Commission/Planning-Commission-Agenda-Packets
# https://www.oshtemo.org/Boards-Committees/Zoning-Board-of-Appeals/ZBA-Agenda-Packets
# https://www.oshtemo.org/Boards-Committees/Downtown-Development-Authority/DDA-Agenda-Packets
# https://www.oshtemo.org/Boards-Committees/Capital-Improvements-Committee/CIC-Agenda-Packets
# https://www.oshtemo.org/Boards-Committees/South-Drake-Road-Corridor-Improvement-Authority/SoDA-Agenda-Packets

civicClerkCheck = "civicclerk.com"  # Check if the URL is from CivicClerk
civicClerkFileTypes = ("Agenda", "Agenda Packet")  # Only keep these kinds of files

#=========================== Data Types ===============================#
class Meeting:
    def __init__(self, title, date, pdf_links):
        self.title = title
        self.date = date
        self.pdf_links = pdf_links

    def has_pdfs(self):
        return len(self.pdf_links) > 0

#=========================== Fetching ===============================#
# Fetch all PDF links from a given HTML webpage (doesn't work for ones that load content dynamically with JavaScript)
def fetch_pdfs_from_html_webpage(url):
    try:
        # 1) Fetch the webpage content (HTML)
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # 2) Parse the HTML content and turn each link that ends with ".pdf" into a meeting (date not read yet)
        soup = BeautifulSoup(response.text, 'html.parser')
        meetings = []
        for link in soup.find_all('a', href=True):
            if link['href'].lower().endswith('.pdf'):
                meetings.append(Meeting(link.get_text(strip=True), None, [urljoin(url, link['href'])]))

        # 3) Return the list of meetings
        return meetings
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# Fetch PDFs from CivicClerk API
def fetch_pdfs_from_civic_clerk(url):
    try:
        # 1) Build the API address from the portal's city name (e.g. "kalamazoomi")
        tenant = urlparse(url).hostname.split(".")[0]
        api = f"https://{tenant}.api.civicclerk.com/v1"

        # 2) Get meetings from today onward, following each "next page" link (15 per page)
        events = []
        next_url = f"{api}/Events"
        params = {"$filter": f"startDateTime ge {date.today()}", "$orderby": "startDateTime"}
        try:
            while next_url:
                response = requests.get(next_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                events += data["value"]
                next_url, params = data.get("@odata.nextLink"), None
        except requests.RequestException as e:
            # Keep the meetings already fetched (later pages can't be reached without this one's "next page" link)
            print(f"Error fetching {next_url}, results may be incomplete: {e}")
        
        # 3) Turn each event into a meeting with its available PDF download links (Not all events have pdfs)
        meetings = []
        for event in events:
            pdf_links = []
            for file in event.get("publishedFiles", []):
                
                # 3.1) Check if the file is a PDF and of the desired type (agenda files), and store the link
                is_pdf = file.get("url", "").lower().endswith(".pdf")
                if is_pdf and file.get("type") in civicClerkFileTypes:
                    link = f"{api}/Meetings/GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
                    pdf_links.append(link)

            # 3.2) Only keep events that have agenda PDFs
            if pdf_links:
                start = datetime.fromisoformat(event["startDateTime"]).date()  # "2026-10-14T18:00:00Z" -> 2026-10-14
                meetings.append(Meeting(event["eventName"], start, pdf_links))

        return meetings
    
    except Exception as e:
        print(f"Error processing CivicClerk data: {e}")
        return None
    
#========================= Main ===============================#
def main():
    print(f"Fetching PDF links from: {testUrl}\n")

    # 1) Fetch all meetings from the given URL
    if civicClerkCheck in testUrl:
        meetings = fetch_pdfs_from_civic_clerk(testUrl)
    else:
        meetings = fetch_pdfs_from_html_webpage(testUrl)

    if not meetings:
        print("No meetings found.")
        return

    # 2) Print each meeting with its PDF links under it
    print(f"Meetings found:\n==============================")
    for meeting in meetings:
        print(f"{meeting.date}  {meeting.title}")
        for link in meeting.pdf_links:
            print(f"    {link}")


if __name__ == "__main__":
    main()
