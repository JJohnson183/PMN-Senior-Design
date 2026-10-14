from datetime import date
from utils import extract_date

#============================ Dates ==============================#

# Check extract_date against many kinds of text
def test_extract_date():
    # 1) Cases it should handle: (text, expected)
    cases = [
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

    # 2) Known gaps: what it should give but doesn't yet (areas to improve)
    knownGaps = [
        ("AgendaOctober 13, 2026", date(2026, 10, 13)),  # Word stuck to the month
    ]

    # 3) Print how many match, and each one that doesn't
    for name, group in (("extract_date cases", cases), ("extract_date known gaps (expected to fail)", knownGaps)):
        fails = [(text, extract_date(text), want) for text, want in group if extract_date(text) != want]
        print(f"{name}: {len(group) - len(fails)}/{len(group)} passed")
        for text, got, want in fails:
            print(f"   FAIL {text!r}: got {got}, wanted {want}")

#=====================================================================#

# Run every test (run "python tests.py")
if __name__ == "__main__":
    test_extract_date()
