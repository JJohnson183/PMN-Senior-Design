import re
from datetime import datetime

#============================ Dates ==============================#

# Text shaped like a date
datePattern = re.compile(
    r"[A-Za-z]+\.?\s*\d{1,2}(?:st|nd|rd|th)?(?:\s*-\s*\d{1,2})?\s*[.,]?\s*\d{4}"  # Month day year: "October 13, 2026", "July11,2022", "Oct 13-14, 2026"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\.?,?\s+\d{4}"                          # Day month year: "14 October 2026"
    r"|\b\d{1,2}[-/.]\d{1,2}[-/.](?:\d{4}|\d{2})\b"                               # Month day year: "10/13/2026", "10-13-26"
    r"|\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"                                             # Year month day: "2026-10-13", "2025.06.24"
)

# Formats to read the cleaned up text with
dateFormats = (
    "%B %d %Y", "%b %d %Y",  # October 13 2026, Oct 13 2026
    "%d %B %Y", "%d %b %Y",  # 13 October 2026, 13 Oct 2026
    "%m/%d/%Y", "%m/%d/%y",  # 10/13/2026, 10/13/26
    "%Y/%m/%d",              # 2026/10/13
)

# Find the first date in a piece of text (e.g. "Regular Meeting: October 26, 2026 @ 7:00 p.m."), or None if there isn't one
def extract_date(text):
    for found in datePattern.findall(text):
        # 1) Clean up the date to match possible date formats
        if re.fullmatch(r"[\d/.-]+", found):
            cleaned = re.sub(r"[-.]", "/", found)  # All numbers: "2025.06.24" -> "2025/06/24"
        else:
            cleaned = re.sub(r"(?<=\d)(st|nd|rd|th)|-\s*\d{1,2}|[.,]", " ", found)  # "Oct. 13th-14, 2026" -> "Oct 13 2026"
            cleaned = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", cleaned)                  # "July11" -> "July 11"
            cleaned = re.sub(r"(?i)\bsept\b", "Sep", cleaned)                        # convert "Sept" to "Sep"
        cleaned = " ".join(cleaned.split())

        # 2) Try each format, words that aren't months (e.g. "Meeting 2 2026") fail every one
        for dateFormat in dateFormats:
            try:
                return datetime.strptime(cleaned, dateFormat).date()
            except ValueError:
                pass
    return None

#=====================================================================#
