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

### 4) Run the script

```
python main.py
```

To check a different website, open `main.py` and change the `testUrl` line near the top:

```python
testUrl = "https://kalamazoomi.portal.civicclerk.com"
```

### 5) Save the output to a file (optional)

`-X utf8` stops Windows from crashing on special characters like ✓. It is not an issue on Mac / Linux.

```
python -X utf8 main.py > result.txt
```

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

- Only reads the first PDF, and only if the meeting is missing a date, time or location.
- Undated PDFs uploaded more than 30 days ago are skipped as too old to be upcoming.
- Only reads page 1 above the first agenda item (e.g. "1. Call to Order").
- Only fills empty fields. Never replaces what came from the site.
- Reads 10 PDFs at a time to keep it fast.

### 4) Drop anything left over

Drops meetings still without a date, or whose PDF date is out of range.