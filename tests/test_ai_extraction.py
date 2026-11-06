import anthropic
import pytest
from datetime import date, time
from types import SimpleNamespace
from pdf.ai_extraction import AgendaFields, check_fields, extract_with_ai

#=====================================================================#
#============================ Fake Claude ==============================#

# A reply that passes every check
validFields = {"date": "2026-10-13", "time": "17:30", "location": "7275 W. Main Street", "summary": "Budget vote."}

# Stands in for client.messages: parse() hands back a set reply (or raises it) instead of calling Claude
class FakeMessages:
    def __init__(self, reply):
        self.reply = reply
        self.request = None

    def parse(self, **request):
        self.request = request  # Kept so a test can check what would have been sent
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply

# Make anthropic.Anthropic() build a fake client for this test only (pytest's monkeypatch undoes it after)
def use_fake_claude(monkeypatch, reply):
    messages = FakeMessages(reply)
    def make_client():
        return SimpleNamespace(messages=messages)
    monkeypatch.setattr(anthropic, "Anthropic", make_client)
    return messages

# A finished reply from Claude holding the given fields
def finished_reply(fields):
    return SimpleNamespace(stop_reason="end_turn", parsed_output=AgendaFields(**fields))

#=====================================================================#
#============================ Checks ==============================#

# A valid reply turns into real date and time values, with nothing rejected
def test_check_fields_valid():
    info = check_fields(AgendaFields(**validFields))
    assert info["date"] == date(2026, 10, 13)
    assert info["time"] == time(17, 30)
    assert info["location"] == "7275 W. Main Street"
    assert info["summary"] == "Budget vote."
    assert info["rejected"] == []

# Each bad value is dropped and named as rejected: (field, bad value)
badValueCases = [
    ("date", "2026-02-30"),  # Not a real day
    ("date", "10/13/2026"),  # Wrong format
    ("time", "25:00"),       # Not a real time
    ("time", "5:30 PM"),     # Not 24-hour
    ("location", "x"),       # Too short
    ("location", "x" * 201), # Too long
    ("summary", ""),         # Empty
    ("summary", "x" * 1001), # Too long
]

@pytest.mark.parametrize("field, badValue", badValueCases)
def test_check_fields_rejects(field, badValue):
    fields = AgendaFields(**validFields)
    setattr(fields, field, badValue)  # Swap in the one bad value
    info = check_fields(fields)
    assert info[field] is None
    assert info["rejected"] == [field]

# Fields Claude says aren't given stay empty and aren't rejected
def test_check_fields_not_given():
    info = check_fields(AgendaFields(date=None, time=None, location=None, summary=None))
    assert info == {"date": None, "time": None, "location": None, "summary": None, "rejected": []}

#=====================================================================#
#============================ Claude call ==============================#

# A finished reply comes back checked
def test_extract_with_ai_good_reply(monkeypatch):
    use_fake_claude(monkeypatch, finished_reply(validFields))
    info = extract_with_ai("Agenda text", "test.pdf")
    assert info["date"] == date(2026, 10, 13)
    assert info["rejected"] == []

# Only the first 3 pages are sent ("\f" marks each new page)
def test_extract_with_ai_sends_first_pages(monkeypatch):
    messages = use_fake_claude(monkeypatch, finished_reply(validFields))
    extract_with_ai("page 1\fpage 2\fpage 3\fpage 4", "test.pdf")
    assert messages.request["messages"][0]["content"] == "page 1\fpage 2\fpage 3"

# A failed call (no key, network) gives None so manual extraction takes over
def test_extract_with_ai_failed_call(monkeypatch):
    use_fake_claude(monkeypatch, Exception("network down"))
    assert extract_with_ai("Agenda text", "test.pdf") is None

# A refusal gives None so manual extraction takes over
def test_extract_with_ai_refusal(monkeypatch):
    use_fake_claude(monkeypatch, SimpleNamespace(stop_reason="refusal", parsed_output=None))
    assert extract_with_ai("Agenda text", "test.pdf") is None

# A PDF with no text (likely scanned) is skipped without calling Claude
def test_extract_with_ai_no_text(monkeypatch):
    messages = use_fake_claude(monkeypatch, finished_reply(validFields))
    assert extract_with_ai("\f\f", "scan.pdf") is None
    assert messages.request is None

#=====================================================================#
