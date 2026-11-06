from fetchers.base import Fetcher
from models import Meeting
from utils.dates import extract_date
import requests
from bs4 import BeautifulSoup # Used for parsing HTML content for extracting links
from urllib.parse import urljoin


#=================================== HTML Page ==============================================#
# A plain web page that lists agenda PDF links (doesn't work for ones that load content dynamically with JavaScript)
class HtmlPageFetcher(Fetcher):
    # Fetch all PDF links from the page, one meeting per link
    def fetch(self, url):
        try:
            # 1) Fetch the webpage content (HTML)
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 2) Parse the HTML content and turn each link that ends with ".pdf" into a meeting
            soup = BeautifulSoup(response.text, 'html.parser')
            meetings = []
            for link in soup.find_all('a', href=True):
                if link['href'].lower().endswith('.pdf'):
                    # 2.1) Date from the link text, otherwise the file name
                    title = link.get_text(strip=True)
                    meeting_date = extract_date(title) or extract_date(link['href'])
                    meetings.append(Meeting(title, meeting_date, [urljoin(url, link['href'])]))

            # 3) Return the list of meetings
            return meetings
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
