param([switch]$DryRun,[string]$Target = "$HOME/.agents/skills")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
foreach ($Skill in @("sponsor-job-agent-dev", "sponsor-job-agent-ops")) {
  $Source = Join-Path $Root "skills/$Skill"; $Dest = Join-Path $Target $Skill
  $Links = Get-ChildItem -Path $Source -Recurse -Force | Where-Object { $_.LinkType }
  if ($Links) { throw "Refusing skill tree containing symlinks: $Source" }
  if ($DryRun) { Write-Host "would install $Skill -> $Dest"; continue }
  New-Item -ItemType Directory -Path $Target -Force | Out-Null
  $Tmp = "$Dest.tmp.$PID"; Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue
  Copy-Item $Source $Tmp -Recurse
  Remove-Item $Dest -Recurse -Force -ErrorAction SilentlyContinue
  Move-Item $Tmp $Dest
  Write-Host "installed $Skill -> $Dest"
}
