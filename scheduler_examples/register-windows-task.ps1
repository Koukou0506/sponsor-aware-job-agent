param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\.."),
    [string]$Time = "08:00"
)
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "data\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c cd /d `"$ProjectRoot`" && `"$Python`" -m job_agent.scheduling run-daily >> `"$LogDir\daily.log`" 2>&1"
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
Register-ScheduledTask -TaskName "SponsorAwareJobAgent" -Action $Action -Trigger $Trigger -Description "Run the local sponsor-aware job scan" -Force
