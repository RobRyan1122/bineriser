@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed --name "Two Colour" --add-data "style.qss:." gui.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)
echo Created dist\Two Colour.exe
pause
