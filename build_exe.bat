@echo off
REM Build-time only: requires PyInstaller (pip install pyinstaller).
REM Produces two one-file executables in dist\:
REM   CleanHomePH.exe    the windowed application
REM   CleanHomeTools.exe console backup and password-reset tools
setlocal
cd /d "%~dp0"
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller is not installed. Run:  python -m pip install pyinstaller
    exit /b 1
)
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name CleanHomePH --paths "%CD%" main.py
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --console ^
    --name CleanHomeTools --paths "%CD%" cleanhome\tools.py
if errorlevel 1 exit /b 1
echo.
echo Built dist\CleanHomePH.exe and dist\CleanHomeTools.exe
