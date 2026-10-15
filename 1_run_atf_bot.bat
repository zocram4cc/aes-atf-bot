@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0"


REM - Call the runner
if exist ".\Engines\atf_bot_run.bat" (
    .\Engines\atf_bot_run.bat 1
) else (
    echo -
    echo - FATAL ERROR - Missing vital file
    echo - The file atf_bot_run.bat was not found in the Engines folder
    echo -
    echo - Please grab a clean simplifier folder
    echo -
    pause
)
