@echo off
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install_windows.ps1"
if errorlevel 1 (
  echo.
  echo Installation failed. Read README_ZH.md or docs\guides\windows-local-setup-zh.md, then rerun this file.
)
pause
