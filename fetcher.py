import requests
from bs4 import BeautifulSoup # Used for parsing HTML content for extracting links
from urllib.parse import urljoin, urlparse
from datetime import date

testUrl = "https://kalamazoomi.portal.civicclerk.com"


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

#=========================== Fetching ===============================#
# Fetch all PDF links from a given HTML webpage (doesn't work for ones that load content dynamically with JavaScript)
def fetch_pdfs_from_html_webpage(url):
    try:
        # 1) Fetch the webpage content (HTML)
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # 2) Parse the HTML content and extract all links that end with ".pdf"
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_links = []
        for link in soup.find_all('a', href=True):
            if link['href'].lower().endswith('.pdf'):
                pdf_links.append(urljoin(url, link['href']))

        # 3) Return the list of PDF links
        return pdf_links
    except requests.RequestException as e:
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
            print(f"Error fetching {next_url}: {e}")
            return None
        
        # 3) Turn each avalible published file into its PDF download link (Not all events have pdfs)
        links = []
        for event in events:
            for file in event.get("publishedFiles", []):
                # Check if the file is a PDF and of the desired type (agenda files)
                is_pdf = file.get("url", "").lower().endswith(".pdf")
                if is_pdf and file.get("type") in civicClerkFileTypes:
                    links.append(f"{api}/Meetings/GetMeetingFileStream(fileId={file['fileId']},plainText=false)")

        return links
    
    except Exception as e:
        print(f"Error processing CivicClerk data: {e}")
        return None

#========================= Processing ===============================#


#========================= Main ===============================#
def main():
    print(f"Fetching PDF links from: {testUrl}\n")

    # 1) Fetch all pdf links from the given URL
    pdf_links = []
    if civicClerkCheck in testUrl:
        pdf_links = fetch_pdfs_from_civic_clerk(testUrl)
    else:
        pdf_links = fetch_pdfs_from_html_webpage(testUrl)

    if not pdf_links: 
        print("No PDF links found.")
        return

    print(f"PDF Links found:\n==============================")
    for link in pdf_links:
        print(link)


   

    



main()













