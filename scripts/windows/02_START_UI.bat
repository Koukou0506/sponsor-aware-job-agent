@echo off
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist ".venv\Scripts\job-agent-ui.exe" (
  echo The app is not installed. Run scripts\windows\01_INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
job-agent-ui
