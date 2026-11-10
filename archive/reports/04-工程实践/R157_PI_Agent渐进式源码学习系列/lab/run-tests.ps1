param(
  [string]$NodePath = '',
  [ValidateSet('all', 'iter00', 'iter01', 'iter02', 'iter03')][string]$Iter = 'all'
)
$ErrorActionPreference = 'Stop'
if (-not $NodePath) { $NodePath = (Get-Command node -ErrorAction Stop).Source }
if (-not (Test-Path -LiteralPath $NodePath)) { throw "Node not found: $NodePath" }
$tests = if ($Iter -eq 'all') { Get-ChildItem "$PSScriptRoot\tests\iter*.test.ts" | Sort-Object Name } else { Get-Item "$PSScriptRoot\tests\$Iter-*.test.ts" }
Push-Location $PSScriptRoot
try { & $NodePath --test @($tests.Name | ForEach-Object { "tests\$_" }); if ($LASTEXITCODE -ne 0) { throw "Tests failed: $LASTEXITCODE" } }
finally { Pop-Location }

