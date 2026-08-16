@echo off
cd /d C:\Users\lukas\Downloads\Martin-1.0

if not exist ".venv\Scripts\activate.bat" (
    echo [Martin] Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [Martin] Waiting for Ollama on http://localhost:11434 ...
setlocal enabledelayedexpansion
set "attempts=0"
:wait_ollama
set /a attempts+=1
curl.exe -s http://localhost:11434/api/tags >nul 2^>^&1
if errorlevel 1 (
    if !attempts! geq 60 (
        echo [Martin] Ollama is not reachable. Start it manually and rerun this shortcut.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto wait_ollama
)
endlocal

echo [Martin] Ensuring gemma3:4b model is available...
curl.exe -s http://localhost:11434/api/tags ^| findstr /i "gemma3:4b" >nul 2^>^&1
if errorlevel 1 (
    echo [Martin] Pulling gemma3:4b model (this may take a minute)...
    ollama pull gemma3:4b
)

echo [Martin] Starting GUI...
python -m app.gui_main
pause
