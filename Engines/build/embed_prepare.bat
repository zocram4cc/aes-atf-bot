@echo off
REM Embeddable Python Builder
REM Automatically downloads and prepares optimized Python distribution

echo Starting embeddable Python builder...
echo.

REM Run the Python script
python "%~dp0embed_prepare.py"

echo.
pause
