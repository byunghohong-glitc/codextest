$ErrorActionPreference = 'Stop'

function Write-ShortError {
  param([string]$Message)
  Write-Host $Message
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$envPath = Join-Path $repoRoot '.env'

if (-not (Test-Path -LiteralPath $envPath)) {
  Write-ShortError 'FIRECRAWL_API_KEY missing.'
  exit 1
}

$apiKey = $null
foreach ($lineRaw in Get-Content -LiteralPath $envPath) {
  if ($null -ne $apiKey) {
    break
  }

  $line = $lineRaw.Trim()
  if (-not $line -or $line.StartsWith('#')) {
    continue
  }

  if ($line -match '^\s*FIRECRAWL_API_KEY\s*=\s*(.*)\s*$') {
    $value = $Matches[1].Trim()
    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
      $value = $value.Substring(1, $value.Length - 2)
    }

    if ([string]::IsNullOrWhiteSpace($value)) {
      continue
    }

    $apiKey = $value
  }
}

if ([string]::IsNullOrWhiteSpace($apiKey)) {
  Write-ShortError 'FIRECRAWL_API_KEY missing.'
  exit 1
}

$env:FIRECRAWL_API_KEY = $apiKey

& npx -y firecrawl-mcp
