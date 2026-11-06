from fetchers.base import Fetcher
from models import Meeting
import requests
from urllib.parse import urlparse
from datetime import date, datetime


civicClerkFileTypes = ("Agenda", "Agenda Packet")  # Only keep these kinds of files

#=================================== CivicClerk ==============================================#
# A CivicClerk portal (e.g. kalamazoomi.portal.civicclerk.com), read through its API
class CivicClerkFetcher(Fetcher):
    # Fetch the portal's meetings from today onward, with their agenda PDF links
    def fetch(self, url):
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
                    next_url = data.get("@odata.nextLink")
                    params = None  # The "next page" link already includes the filters
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

                # 3.2) Join the filled-in address parts: "City Hall, 241 W. South Street, Kalamazoo, MI 49007"
                place = event.get("eventLocation") or {}
                state_zip = f"{place.get('state') or ''} {place.get('zipCode') or ''}".strip()  # "MI 49007"
                parts = [place.get("address1"), place.get("address2"), place.get("city"), state_zip]
                location = ", ".join(part for part in parts if part) or None  # Join the non-blank parts, None if all are blank

                # 3.3) Keep every event, even without PDFs yet
                start = datetime.fromisoformat(event["startDateTime"]).date()  # "2026-10-14T18:00:00Z" -> 2026-10-14
                meetings.append(Meeting(event["eventName"], start, pdf_links, location))

            return meetings

        except Exception as e:
            print(f"Error processing CivicClerk data: {e}")
            return None
