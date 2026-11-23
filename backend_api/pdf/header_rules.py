import re
from datetime import time
from utils.dates import extract_date


#============================ Patterns ==============================#

# Clock times: "5:30 P.M.", "10:00am"
timePattern = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\b\.?", re.I)

# Street addresses: "241 West South Street", "612 N. Park St."
streetPattern = re.compile(
    r"\b\d{2,5}\s+(?:[NSEW]\.?\s+|North\s+|South\s+|East\s+|West\s+)?[A-Za-z]+(?:\s+[A-Za-z]+)?\s+"
    r"(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Way|Parkway|Pkwy|Boulevard|Blvd|Lane|Ln|Court|Ct)\b", re.I)

# A "City, ST 12345" line
cityLinePattern = re.compile(r"^[A-Za-z .]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?$")

# Words in a place name: "Township Hall", "Room 361"
placeWordPattern = re.compile(r"\b(?:Hall|Center|Centre|Room|Chambers|Building|Office|Library)\b", re.I)

# Phone, fax or website (letterhead) lines
contactPattern = re.compile(r"\d{3}[-.)\s]+\d{3}[-.]\d{4}|\bFax\b|\bTele|\bPhone\b|www\.", re.I)

# First agenda item: "1. Call to Order", "A. CALL TO ORDER", "ITEM 1"
firstItemPattern = re.compile(r"^(?:(?:\d{1,2}|[A-Z])\s*[.)–-]\s|ITEM\s+\d|•)")

# Labeled place: "PLACE OF MEETING: ...", "Location: ..."
labelPattern = re.compile(r"(?:PLACE OF MEETING|LOCATION):\s*(.+)", re.I)

# Place after "in-person at": "in-person in room 207A, ..." (may end with the header)
inPersonPattern = re.compile(r"in-person (?:at|in)\s+(?:the\s+)?(.{3,150}?)(?:\s+or virtually|(?<!\b[NSEW])\.(?=\s|$)|$)")

# Place in a sentence: "at the Township Hall to discuss" (a period ends it, but not the one in "W.")
sentencePlacePattern = re.compile(r"\b(?:at|in)\s+(?:the\s+)?([A-Z][^\n]{3,150}?)(?:\s+(?:or virtually|for the purpose|to discuss)|(?<!\b[NSEW])\.(?=\s|$))")

# Leading "AT THE" / "IN THE" before a place name
leadingWordsPattern = re.compile(r"^(?:at|in)\s+the\s+", re.I)

# A line starting with a number: "7275 W. Main Street"
leadingNumberPattern = re.compile(r"\d")

# Online-only meeting: "VIRTUAL ZOOM MEETING"
onlinePattern = re.compile(r"\bvirtual\b|\bzoom meeting\b", re.I)


#============================= Manual Extraction ==============================#
# Date, location and start time from an agenda's first page (None if not found)
def extract_meeting_info(text):
    header = get_header(text)
    return {"date": extract_date(" ".join(header)), "location": extract_location(header), "time": extract_time(header)}


# Non-blank lines on page 1 above the first agenda item
def get_header(text):
    # 1) Keep page 1 only, then drop blank lines and extra spaces
    firstPage = text.split("\f")[0]
    lines = [line.strip() for line in firstPage.splitlines() if line.strip()]

    # 2) Cut at the first agenda item (Common first section headings)
    for i, line in enumerate(lines):
        if firstItemPattern.match(line):
            return lines[:i]
    return lines

# First clock time in the header ("5:30 P.M." -> 17:30), or None
def extract_time(header):
    # 1) Find the time
    found = timePattern.search("\n".join(header))
    if not found:
        return None

    # 2) Convert to 24-hour ("12 A.M." -> 0, "5 P.M." -> 17)
    hour = int(found.group(1)) % 12
    if found.group(3).lower() == "p":
        hour += 12
    return time(hour, int(found.group(2) or 0))

# Meeting place as written in the header, or None (most specific way first)
def extract_location(header):
    # 1) Labeled: "PLACE OF MEETING: ..." (plus the next line if it's a street)
    for i, line in enumerate(header):
        labeled = labelPattern.match(line)
        if labeled:
            parts = [labeled.group(1)]
            if i + 1 < len(header) and leadingNumberPattern.match(header[i + 1]):
                parts.append(header[i + 1])
            return ", ".join(parts)

    # 2) After "in-person at" ("in-person in room 207A, ..."), otherwise in a sentence ("at the Township Hall to discuss")
    joined = " ".join(header)
    found = inPersonPattern.search(joined) or sentencePlacePattern.search(joined)
    if found:
        return found.group(1).rstrip(" ,")

    # 3) Street address line, skipping the letterhead (followed by phone, fax or website)
    for i, line in enumerate(header):
        if not streetPattern.search(line) or contactPattern.search(" ".join(header[i:i + 3])):
            continue

        # 3.1) Add the place name above and "City, ST 12345" below, if there
        parts = [line]
        if i > 0 and placeWordPattern.search(header[i - 1]) and not streetPattern.search(header[i - 1]):
            parts.insert(0, header[i - 1])
        if i + 1 < len(header) and cityLinePattern.match(header[i + 1]):
            parts.append(header[i + 1])

        # 3.2) Drop a leading "AT THE" / "IN THE"
        return leadingWordsPattern.sub("", ", ".join(parts))

    # 4) Online only: "VIRTUAL ZOOM MEETING"
    for line in header:
        if onlinePattern.search(line):
            return line
    return None
