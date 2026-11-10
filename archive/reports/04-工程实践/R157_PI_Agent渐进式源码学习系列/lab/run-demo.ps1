param([string]$NodePath = '')
$ErrorActionPreference = 'Stop'
if (-not $NodePath) { $NodePath = (Get-Command node -ErrorAction Stop).Source }
if (-not (Test-Path -LiteralPath $NodePath)) { throw "Node not found: $NodePath" }
Push-Location $PSScriptRoot
try { & $NodePath "examples\whole-game.ts"; if ($LASTEXITCODE -ne 0) { throw "Demo failed: $LASTEXITCODE" } }
finally { Pop-Location }

