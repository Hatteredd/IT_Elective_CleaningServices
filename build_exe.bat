@echo off
REM Build-time only: requires PyInstaller. Install with: pip install pyinstaller
REM Produces a single-folder or one-file build; adjust spec as needed.
pyinstaller --name CleanHome --onefile --windowed --add-data "cleanhome;cleanhome" --add-data "main.py;." main.py
REM Output in dist\CleanHome.exe
