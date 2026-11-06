import pytest
from datetime import date, time
from pathlib import Path
from utils.dates import extract_date
from pdf.header_rules import extract_meeting_info

#=================================================================#
#============================ Dates ==============================#

# Cases extract_date should handle: (text, expected)
dateCases = [
    # Real link text from Oshtemo and ktwp.org
    ("October 13, 2026 Township Board Agenda Packet(PDF,\xa02MB)", date(2026, 10, 13)),
    ("Regular Board of Trustees Meeting: October 26, 2026 @ 7:00 p.m.", date(2026, 10, 26)),
    ("CANCELED - Work Session: Monday, January 12, 2026 @ 6:00 p.m.", date(2026, 1, 12)),
    ("Special Meeting Notice February 21,2024 @ 5:30", date(2024, 2, 21)),
    ("Board of Trustee Regular Meeting June 13 ,2022", date(2022, 6, 13)),
    ("Work Session Meeting – March 14. 2022", date(2022, 3, 14)),

    # Month written as a word
    ("Oct 13, 2026", date(2026, 10, 13)),
    ("Oct. 13, 2026", date(2026, 10, 13)),
    ("October 13 2026", date(2026, 10, 13)),
    ("October  13,   2026", date(2026, 10, 13)),
    ("OCTOBER 13, 2026", date(2026, 10, 13)),
    ("october 13, 2026", date(2026, 10, 13)),
    ("Oct 1st, 2026", date(2026, 10, 1)),
    ("Oct 2nd, 2026", date(2026, 10, 2)),
    ("Oct 3rd, 2026", date(2026, 10, 3)),
    ("Oct 13th 2026", date(2026, 10, 13)),
    ("Mon, Jan 12, 2026", date(2026, 1, 12)),
    ("Board Meeting July11,2022", date(2022, 7, 11)),
    ("Sept. 3, 2026", date(2026, 9, 3)),
    ("September 3, 2026", date(2026, 9, 3)),

    # Day before month
    ("14 October 2026", date(2026, 10, 14)),
    ("14th Oct. 2026", date(2026, 10, 14)),

    # Month written as a number
    ("Agenda 10/13/2026", date(2026, 10, 13)),
    ("1/5/2026", date(2026, 1, 5)),
    ("01/05/2026", date(2026, 1, 5)),
    ("10-13-2026", date(2026, 10, 13)),
    ("10.13.2026", date(2026, 10, 13)),
    ("10/13/26", date(2026, 10, 13)),
    ("2026-10-13 packet", date(2026, 10, 13)),
    ("2026-1-5", date(2026, 1, 5)),
    ("2026-10-13-township-board-agenda-packet.pdf", date(2026, 10, 13)),
    ("2025.06.24-TB-Agenda-Packet.pdf", date(2025, 6, 24)),

    # More than one date, ranges, or odd days
    ("October 13, 2026 (moved from October 6, 2026)", date(2026, 10, 13)),
    ("October 13-14, 2026", date(2026, 10, 13)),
    ("Oct 13 - 14, 2026", date(2026, 10, 13)),
    ("February 29, 2028", date(2028, 2, 29)),

    # No date in the text
    ("Receipts and Disbursements(PDF, 364KB)", None),
    ("2025 Board Retreat", None),
    ("May 2026 Newsletter", None),
    ("Monday, October 13", None),
    ("Meeting 2 2026", None),
    ("Room 12, 2026", None),
    ("Call 269-375-4260", None),
    ("Version 1.2.3", None),
    ("Packet2 2026", None),
    ("Pages 3-4, 2026", None),
    ("Township Board Meeting", None),
    ("", None),

    # Not real dates
    ("February 30, 2026", None),
    ("February 29, 2026", None),
    ("13/10/2026", None),
]

# Known gaps: what it should give but doesn't yet (areas to improve, expected to fail)
dateKnownGaps = [
    ("AgendaOctober 13, 2026", date(2026, 10, 13)),  # Word stuck to the month
]

# Check extract_date against each case
@pytest.mark.parametrize("text, expected", dateCases)
def test_extract_date(text, expected):
    assert extract_date(text) == expected

# Known gaps are expected to fail until extract_date handles them
@pytest.mark.xfail(reason="known gap")
@pytest.mark.parametrize("text, expected", dateKnownGaps)
def test_extract_date_known_gaps(text, expected):
    assert extract_date(text) == expected

#=====================================================================#
#============================ Meeting info ==============================#

# Page 1 text of real agendas (sources in sources.json)
agendaSamples = Path(__file__).parent / "agenda_samples"

# Cases from real agendas: (sample file, expected location as written, expected time)
meetingInfoCases = [
    # Oshtemo: address block under the board name
    ("oshtemo/township-board-2026-10-27.txt", "7275 W. Main Street, Kalamazoo, MI 49009", time(17, 30)),
    ("oshtemo/township-board-2026-10-13.txt", "7275 W. Main Street, Kalamazoo, MI 49009", time(17, 30)),
    ("oshtemo/township-board-2026-09-29.txt", "7275 West Main Street, Kalamazoo, MI 49009", time(17, 30)),
    ("oshtemo/planning-2026-10-22.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(18, 0)),
    ("oshtemo/planning-2026-10-08.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(18, 0)),
    ("oshtemo/planning-2026-09-24.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(18, 0)),
    ("oshtemo/zba-2026-10-27.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(15, 0)),
    ("oshtemo/zba-2026-09-22.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(15, 0)),
    ("oshtemo/zba-2026-05-26.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(15, 0)),
    ("oshtemo/dda-2026-09-17.txt", "OSHTEMO COMMUNITY CENTER, 6407 PARKVIEW AVENUE", time(15, 0)),
    ("oshtemo/dda-2026-07-30.txt", "OSHTEMO COMMUNITY CENTER, 6407 PARKVIEW AVENUE", time(16, 0)),
    ("oshtemo/dda-2026-07-16.txt", "OSHTEMO COMMUNITY CENTER, 6407 PARKVIEW AVENUE", time(15, 0)),
    ("oshtemo/cic-2024-11-18.txt", "VIRTUAL ZOOM MEETING", time(13, 0)),
    ("oshtemo/cic-2024-05-21.txt", "VIRTUAL ZOOM MEETING", time(13, 0)),
    ("oshtemo/cic-2024-01-16.txt", "VIRTUAL ZOOM MEETING", time(13, 0)),
    ("oshtemo/soda-2026-09-15.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(16, 30)),
    ("oshtemo/soda-2026-09-02.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(12, 0)),
    ("oshtemo/soda-2026-03-04.txt", "OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(12, 0)),
    ("oshtemo/dda-2024-11-21.txt", "OSHTEMO COMMUNITY CENTER, 6407 PARKVIEW AVENUE", time(15, 0)),  # "AT THE ..."
    ("oshtemo/soda-2023-12-06.txt", "LARGE MEETING ROOM AT OSHTEMO TOWNSHIP HALL, 7275 WEST MAIN STREET", time(12, 0)),  # "IN THE ..."

    # City: one line under the date and time
    ("city/environmental-concerns-committ-2026-10-21.txt", "City Commission Chambers – 241 West South Street", time(16, 30)),
    ("city/historic-district-commission-m-2026-10-20.txt", "City Commission Chambers at City Hall – 241 West South Street", time(17, 0)),
    ("city/city-commission-business-meeti-2026-10-19.txt", "City Commission Chambers – 241 West South Street", time(19, 0)),
    ("city/downtown-economic-growth-autho-2026-10-19.txt", "City Hall Community Room - 241 West South Street", time(15, 0)),
    ("city/downtown-development-authority-2026-10-19.txt", "City Hall Community Room — 241 West South Street", time(15, 0)),
    ("city/northside-cultural-business-di-2026-10-15.txt", "Northside Association for Community Development - 612 N. Park St.", time(18, 0)),
    ("city/economic-development-corporati-2026-10-15.txt", "City Hall Community Room — 241 W. South St.", time(7, 45)),
    ("city/brownfield-redevelopment-autho-2026-10-15.txt", "Community Room, City Hall, 241 W South Street", time(7, 45)),
    ("city/brownfield-special-2026-06-25.txt", "Station 2, 1007 E. Alcott St, Community Room", time(8, 0)),

    # County: labeled, in a sentence, or an address block
    ("county/brownfield-redevelopment-autho-2026-10-22.txt", "201 W. Kalamazoo Ave. Kalamazoo, MI 49007 Room 207A", time(15, 0)),
    ("county/brownfield-redevelopment-autho-2026-10-09.txt", "Fishbeck Kalamazoo Office – Fishbeck Training Room, 750 Trade Centre Way, Suite 200, Portage, MI 49002", time(10, 0)),
    ("county/reconvened-statutory-annual-me-2026-10-20.txt", "Board of Commissioners Chambers, second floor, County Administration Building, 201 West Kalamazoo Avenue, Kalamazoo, Michigan", time(18, 30)),
    ("county/finance-and-administration-com-2026-10-02.txt", "Board of Commissioners Room, second floor, County Administration Building, 201 West Kalamazoo Avenue, Kalamazoo, Michigan", time(10, 0)),
    ("county/older-adult-services-advisory-2026-10-14.txt", "Health & Community Services, Room 361, 311 E. Alcott St., Kalamazoo, MI 49001", time(15, 30)),
    ("county/environmental-health-advisory-2026-10-14.txt", "311 East Alcott St, Room 361", time(9, 0)),
    ("county/special-board-facilities-2026-08-28.txt", "Board of Commissioners Conference Room 207a, second floor, County Administration Building, 201 West Kalamazoo Avenue, Kalamazoo, Michigan", time(9, 0)),
    ("county/event-center-assessment-2026-08-28.txt", "Discover Kalamazoo @ 240 W. Michigan Ave., Kalamazoo, MI 49007", time(10, 0)),
    ("county/budget-retreat-2026-07-29.txt", "Expo Center, 2900 Lake St, Kalamazoo, MI 49048, Room B", time(10, 0)),  # "Room B." ends it
    ("county/housing-millage-ad-hoc-2026-07-02.txt", "room 207A, second floor, County Administration Building, 201 West Kalamazoo Avenue, Kalamazoo, MI", time(12, 0)),  # Lowercase start
    ("county/board-appointment-2026-07-30.txt", None, time(14, 0)),  # No place given
    ("county/responsible-bidder-policy-comm-2026-10-21.txt", None, None),  # Page 1 gives neither

    # Kalamazoo Township: place in a sentence
    ("kalamazoo_twp/board-special-2026-10-26.txt", "Kalamazoo Township Hall", time(9, 30)),
    ("kalamazoo_twp/board-regular-2026-10-26.txt", "Kalamazoo Township Hall", time(19, 0)),
    ("kalamazoo_twp/planning-2026-02-05.txt", "Kalamazoo Charter Township Hall, 1720 Riverview Drive, Kalamazoo, MI 49004", time(18, 0)),  # "Location: ..."
    ("kalamazoo_twp/election-commission-2023-10-16.txt", "Township Hall, 1720 Riverview Drive, Kalamazoo, MI 49004", time(17, 15)),

    # Scanned images, no text
    ("county/kalamazoo-county-parks-commiss-2026-10-01.txt", None, None),
    ("kalamazoo_twp/planning-2026-01-08.txt", None, None),
]

# Check extract_meeting_info's location and time against each real agenda
@pytest.mark.parametrize("file, wantLocation, wantTime", meetingInfoCases)
def test_extract_meeting_info(file, wantLocation, wantTime):
    got = extract_meeting_info((agendaSamples / file).read_text(encoding="utf8"))
    assert got["location"] == wantLocation
    assert got["time"] == wantTime

#=====================================================================#
