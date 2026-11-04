# Installs the Agent Forge runner on this Windows machine:
# clones the repo to %USERPROFILE%\agent-forge, records the claude CLI path,
# and registers an hourly scheduled task that runs `forge.py run`.
param(
    [string]$Repo = "zerochance1907/agent-forge",
    [string]$Dir = "$env:USERPROFILE\agent-forge",
    [string]$TaskName = "AgentForge"
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path "$Dir\.git")) {
    gh repo clone $Repo $Dir
} else {
    git -C $Dir pull --rebase
}
New-Item -ItemType Directory -Force "$Dir\logs" | Out-Null

python -c "import forgejury" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install --user --quiet "git+https://github.com/zerochance1907/forgejury"
}

$claude = (Get-Command claude -ErrorAction Stop).Source
@{ claude_path = $claude } | ConvertTo-Json | Set-Content -Encoding utf8 "$Dir\local.json"

schtasks /Create /TN $TaskName /SC HOURLY /TR "`"$Dir\run-forge.cmd`"" /F | Out-Null
Write-Host "Installed. Repo: $Dir  Task: $TaskName (hourly)  Claude: $claude"
Write-Host "Start a cycle now with:  python `"$Dir\forge.py`" new"
