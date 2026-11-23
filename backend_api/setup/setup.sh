#!/bin/sh
# Mac/Linux setup: creates .venv in the project folder if missing, then installs requirements. Safe to run again.
cd "$(dirname "$0")/.." || exit 1

if [ ! -x .venv/bin/python ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv || { echo "Setup failed. Check that python3 is installed."; exit 1; }
fi

echo "Installing requirements..."
.venv/bin/python -m pip install -r setup/requirements.txt || { echo "Setup failed."; exit 1; }

echo "Setup done."
