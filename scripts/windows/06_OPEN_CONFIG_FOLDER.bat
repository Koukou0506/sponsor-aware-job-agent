@echo off
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist "config\local" mkdir "config\local"
explorer.exe "%ROOT%\config\local"
