@echo off
title Phase 4  RAG System
cls

echo.
echo ==================================================
echo   🚀 Phase 4 Advanced RAG System Startup 🚀
echo ==================================================
echo.
echo Starting both Backend and Frontend servers...
echo.

cd /d "%~dp0"

REM Run the Python startup script
".venv\Scripts\python.exe" RUN_SYSTEM.py

echo.
echo System startup complete.
pause