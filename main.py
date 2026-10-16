from fetcher import fetch_meetings
from processor import extract_info_from_pdf


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


def main():
    print(f"Fetching PDF links from: {testUrl}\n")

    # 1) Fetch all meetings from the given URL
    meetings = fetch_meetings(testUrl)

    if not meetings:
        print("No meetings found.")
        return

    # 2) Print each meeting with its PDF links under it
    print(f"Meetings found:\n==============================")
    for meeting in meetings:
        print(f"{meeting.date}  {meeting.title}")
        for link in meeting.pdf_links:
            print(f"    {link}")

    # 3) Extract the information from the PDFs (One for testing)
    result = extract_info_from_pdf(meetings[0].pdf_links[0])
    print(f"\n\n\n\nExtracted text from the first PDF:\n==============================\n{result}")

if __name__ == "__main__":
    main()