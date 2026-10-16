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