@echo off
rem Windows setup: creates .venv in the project folder if missing, then installs requirements. Safe to run again.
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv || goto :fail
)

echo Installing requirements...
".venv\Scripts\python.exe" -m pip install -r setup\requirements.txt || goto :fail

echo.
echo Setup done.
pause
exit /b 0

:fail
echo.
echo Setup failed. Check that Python is installed and on your PATH.
pause
exit /b 1
