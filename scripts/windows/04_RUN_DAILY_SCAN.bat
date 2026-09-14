@echo off
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist ".venv\Scripts\job-agent.exe" (
  echo The app is not installed. Run scripts\windows\01_INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
job-agent run-daily --board-config config\local\boards.yaml
echo.
echo Scan finished. Run scripts\windows\02_START_UI.bat to review results.
pause
