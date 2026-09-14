@echo off
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist ".venv\Scripts\job-agent.exe" (
  echo The app is not installed. Run scripts\windows\01_INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
alembic upgrade head
job-agent doctor
job-agent evaluate-golden tests\golden\jobs\synthetic
python -m compileall -q src
pytest tests\public -q
pause
