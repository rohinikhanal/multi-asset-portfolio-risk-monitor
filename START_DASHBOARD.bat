@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project environment...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo Opening Multi-Asset Portfolio Risk Monitor...
".venv\Scripts\python.exe" -m streamlit run app.py
goto :eof

:error
echo.
echo Setup failed. Check your internet connection and Python installation.
pause
exit /b 1

