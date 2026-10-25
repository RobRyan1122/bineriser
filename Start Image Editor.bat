@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "%~dp0shirtedit.py"
    exit /b
)
python shirtedit.py
if errorlevel 1 pause
