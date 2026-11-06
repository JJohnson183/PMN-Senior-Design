# PMN-Senior-Design

## How to run

### 1) Open a terminal in this folder

```
cd path/to/PMN-Senior-Design
```

### 2) Run the setup script (first time only)

This creates the virtual environment (`.venv`) and installs the requirements.
Run it again only if `setup/requirements.txt` changes.

Windows:

```
setup\setup.bat
```

Mac / Linux:

```
sh setup/setup.sh
```

### 3) Activate the virtual environment (every new terminal)

Windows (PowerShell) (Might need to run `Set-ExecutionPolicy RemoteSigned -Scope Process`):

```
.\.venv\Scripts\Activate.ps1
```

Mac / Linux:

```
source .venv/bin/activate
```

You will see `(.venv)` at the start of the terminal line when it is active.

### 4) Set the AI key (optional)

The AI (Claude) reads each agenda PDF and writes a short summary. Without a key everything
still runs: each PDF prints a notice and manual extraction is used instead. Each run with a
key costs a little money. Never put the key in the code please.

Windows (PowerShell), for this terminal only:

```
$env:ANTHROPIC_API_KEY = "api-key"
```

Mac / Linux:

```
export ANTHROPIC_API_KEY="api-key"
```

### 5) Run the script

```
python main.py
```

To check a different website, open `main.py` and change the `testUrl` line near the top:

```python
testUrl = "https://kalamazoomi.portal.civicclerk.com"
```

### 6) Save the output to a file (optional)

`-X utf8` stops Windows from crashing on special characters like ✓. It is not an issue on Mac / Linux.

```
python -X utf8 main.py > result.txt
```

### 7) Run the tests

```
pytest
```

Every case should pass. Known gaps show as `xfailed` (expected to fail). The tests never
call the AI, so they need no key and cost nothing.

## How it works

### 1) Fetch the meetings

- **CivicClerk sites** (City of Kalamazoo, Kalamazoo County): uses the CivicClerk API.
  - Only gets meetings from today onward.
  - Only keeps "Agenda" and "Agenda Packet" PDFs.
  - Takes the title, date and location from the API. Keeps every meeting, even ones without PDFs yet.
- **Other sites** (Oshtemo Township, ect): reads the webpage and turns each link ending in `.pdf` into a meeting.
  - Date comes from the link text, otherwise the file name.
  - Doesn't work for sites that load their links/content with JavaScript dynamiclly.

### 2) Drop meetings out of range

Drops meetings before today or more than a year ahead (a year ahead is likely a typo like "2108" for "2018"). Undated meetings are kept for now, since their PDF may have a date.

### 3) Fill missing info from the PDF

- Only reads the first PDF, and only if the meeting is missing a date, time, location or summary.
- Undated PDFs uploaded more than 30 days ago are skipped as too old to be upcoming.
- Sends the first 3 pages to the AI for the date, time, location and a summary. Each answer is checked (a real date and time, length limits).
- If the AI fails, or leaves a field empty, or a field fails its check, manual extraction fills it. Manual extraction only reads page 1 above the first agenda item (e.g. "1. Call to Order").
- Only fills empty fields. Never replaces what came from the site.
- Reads 10 PDFs at a time to keep it fast.

### 4) Drop anything left over

Drops meetings still without a date, or whose PDF date is out of range.

## AI model

Uses **Claude Haiku 5.5** (`aiModel` in `pdf/ai_extraction.py`).

- **Why:** it is the cheapest current Claude model and is made for simple, high-volume jobs like reading a few fields from an agenda. In testing it did as well as Sonnet 5.5, which costs 20 times more.
- **Price:** $0.10 per million tokens sent and $0.50 per million tokens written back (a token is about 4 characters).
- **Estimated use:** each PDF sends about 1,150 tokens and gets up to about 600 back, so about $0.02 to $0.04 per 100 PDFs. A run only reads PDFs for meetings whose agenda is posted, and agendas usually go up about a week ahead, so each run reads only a handful. Even daily runs cost a few cents a month.
- **Testing so far:** without an API key, Haiku and Sonnet each read 47 real sample agendas. Both got every date and time right and nearly every location, and wrote accurate summaries. Tested with seperate Claude plan, real API calls are not tested yet.