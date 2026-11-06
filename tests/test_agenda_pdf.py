from datetime import date, time
from pathlib import Path
import pdf.agenda_pdf as agenda_pdf
from pdf.agenda_pdf import AgendaPdf
from pdf.header_rules import extract_meeting_info

#=====================================================================#
#============================ Fakes ==============================#

# A real agenda's page 1, so manual extraction has values to fall back on
sampleText = (Path(__file__).parent / "agenda_samples" / "oshtemo/township-board-2026-10-27.txt").read_text(encoding="utf8")
manualInfo = extract_meeting_info(sampleText)

# What the AI gives when every field passes its check (time and location differ from manual extraction)
aiInfo = {"date": date(2026, 10, 27), "time": time(18, 0), "location": "Township Hall", "summary": "Budget vote.", "rejected": []}

# Make the PDF's text and the AI's answer fixed for this test only (no download, no API call)
def use_fakes(monkeypatch, pdfText, aiResult):
    def fake_text(self):
        return pdfText
    def fake_ai(text, url):
        return aiResult
    monkeypatch.setattr(AgendaPdf, "text", fake_text)
    monkeypatch.setattr(agenda_pdf, "extract_with_ai", fake_ai)

#=====================================================================#
#============================ Meeting info ==============================#

# The AI's answer is used as is when every field passes
def test_meeting_info_uses_ai(monkeypatch):
    use_fakes(monkeypatch, sampleText, aiInfo)
    info = AgendaPdf("test.pdf").meeting_info()
    assert info == {"date": date(2026, 10, 27), "location": "Township Hall", "time": time(18, 0), "summary": "Budget vote."}

# The AI fails: manual extraction fills every field, with no summary
def test_meeting_info_ai_failed(monkeypatch):
    use_fakes(monkeypatch, sampleText, None)
    info = AgendaPdf("test.pdf").meeting_info()
    assert info["date"] == manualInfo["date"]
    assert info["location"] == manualInfo["location"]
    assert info["time"] == manualInfo["time"]
    assert info["summary"] is None

# One AI field fails its check: manual extraction fills only that field
def test_meeting_info_rejected_field(monkeypatch):
    rejectedTime = aiInfo.copy()
    rejectedTime["time"] = None
    rejectedTime["rejected"] = ["time"]
    use_fakes(monkeypatch, sampleText, rejectedTime)
    info = AgendaPdf("test.pdf").meeting_info()
    assert info["time"] == manualInfo["time"]
    assert info["location"] == "Township Hall"
    assert info["summary"] == "Budget vote."

# The AI leaves a field empty: manual extraction fills it
def test_meeting_info_empty_field(monkeypatch):
    noLocation = aiInfo.copy()
    noLocation["location"] = None
    use_fakes(monkeypatch, sampleText, noLocation)
    info = AgendaPdf("test.pdf").meeting_info()
    assert info["location"] == manualInfo["location"]
    assert info["time"] == time(18, 0)

# A PDF that can't be downloaded or read gives None
def test_meeting_info_unreadable_pdf(monkeypatch):
    use_fakes(monkeypatch, None, aiInfo)
    assert AgendaPdf("test.pdf").meeting_info() is None

#=====================================================================#
