import anthropic
from datetime import datetime
from pydantic import BaseModel, Field


aiModel = "claude-opus-5-5"  # Placeholder until the best simple one is picked
aiPages = 3  # Pages sent to the AI (the agenda is usually in the first few)
maxLocationLength = 200
maxSummaryLength = 1000

# What the AI is asked to do (the fields it fills are in AgendaFields) (Will be adjusted later)
aiPrompt = (
    "Read the first pages of a public meeting agenda from a Michigan city, county or township. "
    "Give the meeting's date, start time and location as the agenda states them, and a 2 to 3 "
    "sentence summary in plain language of what the meeting will cover. "
    "Use null for any field the agenda doesn't state. Never guess."
)

#============================= Fields ==============================#
# The fields the AI must fill (each description is sent to the AI as part of the request)
class AgendaFields(BaseModel):
    date: str | None = Field(description="Meeting date as YYYY-MM-DD, e.g. 2026-10-13")
    time: str | None = Field(description="Start time as 24-hour HH:MM, e.g. 17:30")
    location: str | None = Field(description="Meeting place as written, e.g. 7275 W. Main Street, Kalamazoo, MI 49009")
    summary: str | None = Field(description="2 to 3 sentences on what the meeting will cover")

#============================= Checks ==============================#
# Turn the AI's text into real values we can use ("rejected" names each field that failed its check)
def check_fields(fields):
    info = {"date": None, "time": None, "location": None, "summary": None, "rejected": []}

    # 1) Check the date is a real calendar date ("2026-02-30" fails)
    if fields.date is not None:
        try:
            info["date"] = datetime.strptime(fields.date, "%Y-%m-%d").date()
        except ValueError:
            info["rejected"].append("date")

    # 2) Check the time is a real 24-hour time ("25:00" fails)
    if fields.time is not None:
        try:
            info["time"] = datetime.strptime(fields.time, "%H:%M").time()
        except ValueError:
            info["rejected"].append("time")

    # 3) Check the location and summary are within their length limits
    if fields.location is not None:
        if 3 <= len(fields.location) <= maxLocationLength:
            info["location"] = fields.location
        else:
            info["rejected"].append("location")
    if fields.summary is not None:
        if 1 <= len(fields.summary) <= maxSummaryLength:
            info["summary"] = fields.summary
        else:
            info["rejected"].append("summary")

    return info

#============================= AI Extraction ==============================#
# Read the date, time, location and summary with the AI (Claude here), or None if it fails
def extract_with_ai(text, url):
    # 1) Keep the first pages, skipping PDFs with no text
    firstPages = "\f".join(text.split("\f")[:aiPages])
    if not firstPages.strip():
        print(f"AI skipped {url} (no text), using manual extraction instead")
        return None

    # 2) Send the pages to Claude and get the fields back
    try:
        client = anthropic.Anthropic()  # Reads the key from the ANTHROPIC_API_KEY environment variable
        response = client.messages.parse(
            model=aiModel,
            max_tokens=4000,
            output_config={"effort": "low"},  # Low effort keeps it cheap
            system=aiPrompt,
            messages=[{"role": "user", "content": firstPages}],
            output_format=AgendaFields,
        )
    except Exception as e:
        print(f"AI couldn't read {url} ({e}), using manual extraction instead")
        return None

    # 3) Stop if Claude refused or was cut off
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        print(f"AI couldn't read {url} (stopped: {response.stop_reason}), using manual extraction instead")
        return None

    # 4) Check each field, naming any that fail
    info = check_fields(response.parsed_output)
    for name in info["rejected"]:
        print(f"AI {name} for {url} failed its check, using manual extraction instead")
    return info
