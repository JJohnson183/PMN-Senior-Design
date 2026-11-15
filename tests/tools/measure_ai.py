import os
import re
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from collections import Counter
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # Lets this script in tests/tools/ import the project's code

import anthropic
import anthropic.resources.messages.messages as messagesModule
import pdf.agenda_pdf as agendaPdfModule
import pipeline
from pdf.agenda_pdf import AgendaPdf
from pdf.ai_extraction import extract_with_ai, check_fields, aiPages, maxLocationLength, maxSummaryLength
from tests.test_extraction import meetingInfoCases, agendaSamples


# Measures the real AI calls (time, tokens, cost, answers) and saves them to results/ beside it. Costs money, so never name it test_*.py (pytest would run it).
# Run from PMN-Senior-Design: python -X utf8 tests/tools/measure_ai.py <mode>   (modes below)

#============================= Settings ==============================#
# Haiku 5.5 prices in US dollars per million tokens, from Anthropic's price list as of 2026-11-03 (prompts under 100K tokens)
inputPricePerMillion = 0.10
outputPricePerMillion = 0.50  # Thinking tokens are billed as output
resultsFolder = Path(__file__).parent / "results"
fieldNames = ("date", "time", "location", "summary")

# One sample per kind of site, for a cheap first check
quickSamples = [
    "city/city-commission-business-meeti-2026-10-19.txt",
    "county/finance-and-administration-com-2026-10-02.txt",
    "oshtemo/planning-2026-10-22.txt",
]

# The sites listed in main.py
sites = [
    "https://kalamazoomi.portal.civicclerk.com",
    "https://kalamazoocomi.portal.civicclerk.com",
    "https://www.ktwp.org/board-of-trustees-meetings/",
    "https://www.oshtemo.org/Boards-Committees/Township-Board/Township-Board-Agenda-Packets",
    "https://www.oshtemo.org/Boards-Committees/Planning-Commission/Planning-Commission-Agenda-Packets",
    "https://www.oshtemo.org/Boards-Committees/Zoning-Board-of-Appeals/ZBA-Agenda-Packets",
    "https://www.oshtemo.org/Boards-Committees/Downtown-Development-Authority/DDA-Agenda-Packets",
    "https://www.oshtemo.org/Boards-Committees/Capital-Improvements-Committee/CIC-Agenda-Packets",
    "https://www.oshtemo.org/Boards-Committees/South-Drake-Road-Corridor-Improvement-Authority/SoDA-Agenda-Packets",
]

# What each mode does (the counts come from the lists, so they stay right)
modes = {
    "quick": f"{len(quickSamples)} samples, page 1 only",
    "samples": f"all {len(meetingInfoCases)} samples, page 1 only",
    "packets": f"all {len(meetingInfoCases)} samples, the real PDFs (first pages sent, like the real flow)",
    "baseline": f"{len(sites)} sites with the AI off, free",
    "sites": f"{len(sites)} sites with the AI on",
}

#============================= Calculations ==============================#
# Cost of one call in US dollars: each token count times its price per token
def call_cost(inputTokens, outputTokens):
    inputCost = inputTokens * inputPricePerMillion / 1_000_000
    outputCost = outputTokens * outputPricePerMillion / 1_000_000
    return round(inputCost + outputCost, 7)  # Rounded so it reads 0.0002327, not 0.00023270000000000002

# Average of a list of numbers (0 if the list is empty)
def average(values):
    return sum(values) / len(values) if values else 0

# Pages in the PDF ("\f" marks each new page), and how many the AI is sent (0 if it wasn't called)
def page_counts(text, aiCalled):
    pdfPages = text.count("\f") + 1
    pagesSent = min(pdfPages, aiPages) if aiCalled else 0
    return pdfPages, pagesSent

# Expected date: from the sample's file name, or none if the pages sent to the AI have no text (scanned)
def expected_date(file, text):
    firstPages = "\f".join(text.split("\f")[:aiPages])
    return file[-14:-4] if firstPages.strip() else None

# Lowercase and drop punctuation, so "Room 207A," matches "room 207a"
def plain(text):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()) if text else None

# "same" as expected, "fuller" if it holds the expected text plus more (like the city and zip), else "different"
def location_match(got, expected):
    if plain(got) == plain(expected):
        return "same"
    if got and expected and plain(expected) in plain(got):
        return "fuller"
    return "different"

# Where a field's final value came from: the site, the AI, manual extraction, or nowhere
def field_source(name, fromSite, ai, manual):
    aiFields = (ai or {}).get("aiFields") or {}
    aiRejected = (ai or {}).get("rejectedFields") or []
    aiFinished = (ai or {}).get("stopReason") == "end_turn"  # A cut-off or refused answer is thrown away, so manual fills in
    if fromSite[name] is not None:
        return "site"
    if aiFinished and aiFields.get(name) is not None and name not in aiRejected:
        return "ai"
    if manual and manual.get(name) is not None:
        return "manual"
    return "none"

# One AI call's numbers, to show beside its result (all None if the AI wasn't called)
def call_stats(call):
    call = call or {}
    return {
        "aiCalled": bool(call),
        "seconds": call.get("seconds"),
        "inputTokens": call.get("inputTokens"),
        "outputTokens": call.get("outputTokens"),
        "thinkingTokens": call.get("thinkingTokens"),
        "cost": call.get("cost"),
        "stopReason": call.get("stopReason"),
        "rejectedFields": call.get("rejectedFields"),
        "error": call.get("error"),
    }

# Score of a samples run: how many dates and times were right, and how the locations matched
def sample_score(results):
    scored = [result for result in results if not result.get("unreadable")]
    locations = Counter(result["locationMatch"] for result in scored)
    return {
        "scored": len(scored),
        "unreadable": len(results) - len(scored),
        "dateOk": sum(result["dateOk"] for result in scored),
        "timeOk": sum(result["timeOk"] for result in scored),
        "locationSame": locations["same"],
        "locationFuller": locations["fuller"],
        "locationDifferent": locations["different"],
    }

# Totals across every AI call this run
def call_totals(calls):
    # 1) Keep the calls that worked
    good = [call for call in calls if "error" not in call]
    errors = len(calls) - len(good)
    if not good:
        return {"calls": len(calls), "errors": errors}

    # 2) Pull out each number
    allSeconds = [call["seconds"] for call in good]
    inputTokens = [call["inputTokens"] for call in good]
    outputTokens = [call["outputTokens"] for call in good]
    thinkingTokens = [call["thinkingTokens"] or 0 for call in good]
    costs = [call["cost"] for call in good]

    # 3) Add them up
    return {
        "calls": len(calls),
        "errors": errors,
        "secondsAverage": round(average(allSeconds), 2),
        "secondsLongest": max(allSeconds),
        "inputTokensAverage": round(average(inputTokens)),
        "outputTokensAverage": round(average(outputTokens)),
        "outputTokensLongest": max(outputTokens),
        "thinkingTokensAverage": round(average(thinkingTokens)),
        "callsThatThought": sum(tokens > 0 for tokens in thinkingTokens),
        "costTotal": round(sum(costs), 7),
        "costPerCall": round(average(costs), 7),
        "repliesCutOffOrRefused": sum(call["stopReason"] != "end_turn" for call in good),
        "fieldsThatFailedChecks": sum(len(call.get("rejectedFields") or []) for call in good),
    }

#============================= Stopwatch ==============================#
# While this script runs, these stand in for parts of the project's code: each runs the real part and records what happened
calls = []  # One entry per AI call
pdfs = []  # One entry per PDF the full flow read
aiSettings = {}  # What the first AI call sent (the same for every call)
recordLock = threading.Lock()  # Sites read 10 PDFs at once, so entries are added one at a time
current = threading.local()  # What this thread is working on, so each record knows its PDF

originalParse = messagesModule.Messages.parse
originalManual = agendaPdfModule.extract_meeting_info
originalFill = pipeline.fill_missing_info

# What an AI call sends: model, prompt, each field asked for with its description, and limits
def sent_settings(messages, settings):
    fieldsAsked = settings["output_format"].model_json_schema()["properties"]
    return {
        "model": settings["model"],
        "prompt": settings["system"],
        "fieldsAsked": {name: field.get("description") for name, field in fieldsAsked.items()},
        "outputConfig": settings.get("output_config"),
        "maxTokens": settings["max_tokens"],
        "timeoutSeconds": messages._client.timeout,
        "retries": messages._client.max_retries,
        "anthropicLibrary": anthropic.__version__,
    }

# Stands in for the library's AI call: times it, notes tokens, cost and answer, then hands the reply back unchanged
def timed_parse(self, **settings):
    # 1) Save what the call sends (once per run), then time the call
    with recordLock:
        if not aiSettings:
            aiSettings.update(sent_settings(self, settings))
    record = {"url": getattr(current, "url", None)}
    current.ai = record
    start = time.perf_counter()
    try:
        response = originalParse(self, **settings)
    except Exception as e:
        record["seconds"] = round(time.perf_counter() - start, 2)
        record["error"] = str(e)
        with recordLock:
            calls.append(record)
        raise
    record["seconds"] = round(time.perf_counter() - start, 2)

    # 2) Note the tokens, cost, why it stopped, and the fields it gave
    usage = response.usage
    details = usage.output_tokens_details
    record["inputTokens"] = usage.input_tokens
    record["outputTokens"] = usage.output_tokens
    record["thinkingTokens"] = details.thinking_tokens if details else None  # Part of outputTokens
    record["cost"] = call_cost(usage.input_tokens, usage.output_tokens)
    record["stopReason"] = response.stop_reason
    if response.parsed_output is not None:
        record["aiFields"] = response.parsed_output.model_dump()
        record["rejectedFields"] = check_fields(response.parsed_output)["rejected"]
    with recordLock:
        calls.append(record)
    return response

# Stands in for manual extraction: runs the real one and keeps its answer and the PDF's text for this thread's record
def manual_with_record(text):
    current.text = text
    manual = originalManual(text)
    current.manual = dict(manual)  # Keep a copy, since meeting_info adds a summary to the one it gets back
    return manual

# Stands in for pipeline.fill_missing_info: runs the real one, then records where each field came from
def fill_with_record(meeting):
    # 1) Note what the site already gave, then run the real fill
    fromSite = {name: getattr(meeting, name) for name in fieldNames}
    current.url = meeting.pdf_links[0] if meeting.has_pdfs() else None
    current.ai = current.manual = current.text = None
    read = originalFill(meeting)
    if not read:
        return read

    # 2) Record the PDF: its pages, the AI call's numbers, and each field's value and source
    pdfPages, pagesSent = page_counts(current.text or "", aiCalled=current.ai is not None)
    final = {name: getattr(meeting, name) for name in fieldNames}
    sources = {name: field_source(name, fromSite, current.ai, current.manual) for name in fieldNames}
    with recordLock:
        pdfs.append({
            "title": meeting.title,
            "url": current.url,
            "pdfPages": pdfPages,
            "pagesSent": pagesSent,
            **call_stats(current.ai),
            "source": sources,
            "fromSite": fromSite,
            "aiFields": (current.ai or {}).get("aiFields"),
            "manualFields": current.manual,
            "final": final,
        })
    return read

# Swap in the stand-ins (and turn the AI off for the baseline) for this run only
def install_stopwatch(useAi):
    messagesModule.Messages.parse = timed_parse
    agendaPdfModule.extract_meeting_info = manual_with_record
    pipeline.fill_missing_info = fill_with_record
    if not useAi:
        agendaPdfModule.extract_with_ai = lambda text, url: None  # Same as the AI failing, so manual extraction is used

#============================= Runs ==============================#
# Send each sample to the AI (page 1 text, or the real PDF if fromPdf) and score it against the tests' expected values
def run_samples(cases, fromPdf=False):
    sources = json.loads((agendaSamples / "sources.json").read_text(encoding="utf8"))
    results = []
    for file, expectedLocation, expectedTime in cases:
        # 1) Get the text: the saved page 1, or the real PDF downloaded again
        url = sources[file]
        text = AgendaPdf(url).extract_text() if fromPdf else (agendaSamples / file).read_text(encoding="utf8")
        if text is None:
            results.append({"file": file, "unreadable": True})
            print(f"{file}: PDF couldn't be downloaded or read, not scored")
            continue

        # 2) Send it to the AI
        current.url = url
        current.ai = None
        info = extract_with_ai(text, url) or {"date": None, "time": None, "location": None, "summary": None}

        # 3) Compare with the expected values
        expectedDate = expected_date(file, text)
        gotDate = str(info["date"]) if info["date"] else None
        pdfPages, pagesSent = page_counts(text, aiCalled=current.ai is not None)
        result = {
            "file": file,
            "pdfPages": pdfPages,
            "pagesSent": pagesSent,
            **call_stats(current.ai),
            "expectedDate": expectedDate,
            "gotDate": gotDate,
            "dateOk": gotDate == expectedDate,
            "expectedTime": expectedTime,
            "gotTime": info["time"],
            "timeOk": info["time"] == expectedTime,
            "expectedLocation": expectedLocation,
            "gotLocation": info["location"],
            "locationMatch": location_match(info["location"], expectedLocation),
            "summaryLength": len(info["summary"]) if info["summary"] else 0,
            "summary": info["summary"],
        }
        results.append(result)
        print(f"{file}: date {'ok' if result['dateOk'] else 'WRONG'}, time {'ok' if result['timeOk'] else 'WRONG'}, "
              f"location {result['locationMatch']} ({info['location']})")

    # 4) Print the score
    score = sample_score(results)
    print(f"\nScore: date {score['dateOk']} / {score['scored']}, time {score['timeOk']} / {score['scored']}, "
          f"location {score['locationSame']} same + {score['locationFuller']} fuller / {score['scored']} "
          f"({score['locationDifferent']} different), {score['unreadable']} unreadable")
    return score, results

# Run every site through the real flow, timing each one
def run_sites():
    results = []
    for url in sites:
        # 1) Run the site and time it
        print(f"\n===== {url}")
        callsBefore, pdfsBefore = len(calls), len(pdfs)
        start = time.perf_counter()
        meetings = pipeline.get_meetings(url) or []
        seconds = round(time.perf_counter() - start, 1)

        # 2) Count the site's AI calls and where each field came from
        siteCalls = calls[callsBefore:]
        sitePdfs = pdfs[pdfsBefore:]
        siteCost = sum(call.get("cost", 0) for call in siteCalls)
        sources = {name: dict(Counter(pdf["source"][name] for pdf in sitePdfs)) for name in fieldNames}
        withTime = sum(meeting.time is not None for meeting in meetings)
        withLocation = sum(meeting.location is not None for meeting in meetings)
        withSummary = sum(meeting.summary is not None for meeting in meetings)

        # 3) Save and print it
        results.append({
            "site": url,
            "seconds": seconds,
            "aiCalls": len(siteCalls),
            "cost": siteCost,
            "meetingsKept": len(meetings),
            "withTime": withTime,
            "withLocation": withLocation,
            "withSummary": withSummary,
            "sourcesForPdfsRead": sources,
            "pdfs": sitePdfs,
            "meetings": [vars(meeting) for meeting in meetings],
        })
        print(f"{len(meetings)} meetings in {seconds}s: {withTime} with a time, {withLocation} with a location, "
              f"{withSummary} with a summary, {len(siteCalls)} AI calls")
        if sitePdfs:
            print(f"Where the {len(sitePdfs)} PDFs' fields came from: {sources}")
    return None, results

#============================= Output ==============================#
# Prints to the screen and a log file at once
class Tee:
    # Keep the places to print to (the screen and the log)
    def __init__(self, *streams):
        self.streams = streams

    # Print the text to each place
    def write(self, text):
        for stream in self.streams:
            stream.write(text)

    # Make sure each place shows everything printed so far
    def flush(self):
        for stream in self.streams:
            stream.flush()

# Run the chosen mode and save its results and log
def main():
    # 1) Check the mode, and the key for modes that call the AI
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in modes:
        print("Use one of:\n" + "\n".join(f"  {name}: {about}" for name, about in modes.items()))
        return
    if mode != "baseline" and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY isn't set in this terminal")
        return

    # 2) Save everything printed to a log beside the results (printing goes back to normal when the block ends)
    resultsFolder.mkdir(exist_ok=True)
    name = f"{mode}-{datetime.now():%Y-%m-%d-%H%M%S}"  # Seconds too, so two runs in the same minute don't overwrite
    with open(resultsFolder / f"{name}.log", "w", encoding="utf8") as log, redirect_stdout(Tee(sys.stdout, log)):
        # 3) Run it, timing the whole run
        install_stopwatch(useAi=mode != "baseline")
        start = time.perf_counter()
        if mode == "quick":
            score, results = run_samples([case for case in meetingInfoCases if case[0] in quickSamples])
        elif mode in ("samples", "packets"):
            score, results = run_samples(meetingInfoCases, fromPdf=mode == "packets")
        else:
            score, results = run_sites()
        totalSeconds = round(time.perf_counter() - start, 1)

        # 4) Print the totals and save the results, with what the run was based on first (score is only for sample runs)
        totals = call_totals(calls)
        print(f"\nAI calls: {json.dumps(totals, indent=1)}")
        print(f"Whole run took {totalSeconds}s")
        saved = {
            "mode": f"{mode}: {modes[mode]}",
            "ranAt": datetime.now().isoformat(timespec="seconds"),
            "totalSeconds": totalSeconds,
            "aiSettings": aiSettings or "AI off or never called",
            "maxPagesSentPerPdf": aiPages,
            "maxCharacters": {"location": maxLocationLength, "summary": maxSummaryLength},
            "pricePerMillionTokens": {"input": inputPricePerMillion, "output": outputPricePerMillion},
            "score": score,
            "totals": totals,
            "results": results,
        }
        if score is None:
            del saved["score"]  # Site runs have nothing to score against
        (resultsFolder / f"{name}.json").write_text(json.dumps(saved, indent=1, default=str, ensure_ascii=False), encoding="utf8")
        print(f"Saved {name}.json and {name}.log in the results folder")


if __name__ == "__main__":
    main()
