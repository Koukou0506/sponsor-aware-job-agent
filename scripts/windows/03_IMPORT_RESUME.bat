@echo off
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist ".venv\Scripts\job-agent.exe" (
  echo The app is not installed. Run scripts\windows\01_INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
set "RESUME=%~1"
if "%RESUME%"=="" set /p "RESUME=Paste the full path of the PDF/DOCX/TXT/MD resume: "
if "%RESUME%"=="" exit /b 1
call ".venv\Scripts\activate.bat"
job-agent resume import "%RESUME%"
echo.
echo Import created a pending review session. Open the UI and approve extracted facts.
pause
