from pipeline import get_meetings


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

def print_meeting_info(meetings):
    for meeting in meetings:
        # 1) Print the meeting's basic information
        print(f"\nTitle: {meeting.title}")
        print(f"Date: {meeting.date}")
        print(f"Time: {meeting.time}")
        print(f"Location: {meeting.location}")
        print(f"PDF Links: {meeting.pdf_links}")

    # 2) Print a summary of the meetings
    with_pdfs = sum(meeting.has_pdfs() for meeting in meetings)
    dated = sum(meeting.date is not None for meeting in meetings)
    timed = sum(meeting.time is not None for meeting in meetings)
    located = sum(meeting.location is not None for meeting in meetings)
    print(f"\nSummary:\n==============================")
    print(f"{len(meetings)} meetings: {with_pdfs} with PDFs, {dated} with a date, {timed} with a time, {located} with a location")

def main():
    print(f"Fetching PDF links from: {testUrl}\n")

    # 1) Fetch the upcoming meetings from the given URL, with missing info filled from their PDFs
    meetings = get_meetings(testUrl)

    if not meetings:
        print("No meetings found.")
        return

    # Temp prints
    print_meeting_info(meetings)


if __name__ == "__main__":
    main()