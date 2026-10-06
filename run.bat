@echo off
REM ============================================================
REM  LeakedIn — One-command dev launcher (Windows)
REM  Usage: run.bat
REM  Starts backend (FastAPI) + frontend (static file server)
REM ============================================================

setlocal

set "REPO_ROOT=%~dp0"
set "PYTHONPATH=%REPO_ROOT%"

echo.
echo  ==========================================
echo   LeakedIn — Starting development servers
echo  ==========================================
echo.

REM ── Check Virtual Environment ────────────────────────────
if exist "%REPO_ROOT%\.venv\Scripts\activate.bat" (
    set "ACTIVATE_CMD=call ""%REPO_ROOT%\.venv\Scripts\activate.bat"" && "
    set "PY_CMD=""%REPO_ROOT%\.venv\Scripts\python.exe"""
    set "UVICORN_CMD=""%REPO_ROOT%\.venv\Scripts\python.exe"" -m uvicorn"
) else (
    set "ACTIVATE_CMD="
    set "PY_CMD=python"
    set "UVICORN_CMD=uvicorn"
)

REM ── 1. Backend (FastAPI via Uvicorn) ───────────────────────
echo  [1/2] Starting backend API on http://localhost:8000 ...
start "LeakedIn-Backend" cmd /k "cd /d %REPO_ROOT% && %ACTIVATE_CMD%set PYTHONPATH=. && %UVICORN_CMD% backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

REM ── 2. Frontend (Python static server) ─────────────────────
echo  [2/2] Starting frontend on http://localhost:5500 ...
start "LeakedIn-Frontend" cmd /k "cd /d %REPO_ROOT% && %ACTIVATE_CMD%%PY_CMD% -m http.server 5500 --directory frontend"

echo.
echo  Both servers are starting in separate windows.
echo.
echo  Frontend : http://localhost:5500
echo  API Docs : http://localhost:8000/docs
echo  Health   : http://localhost:8000/health
echo.
echo  Press any key to exit this launcher (servers keep running).
pause >nul

endlocal
