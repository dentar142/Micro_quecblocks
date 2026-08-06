param(
    [string]$Output = "Micro_quecblocks.zip"
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$OutPath = if ([IO.Path]::IsPathRooted($Output)) { $Output } else { Join-Path $Repo $Output }
$Stage = Join-Path $env:TEMP ("micro-quecblocks-" + [guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Path $Stage | Out-Null
try {
    $GitFiles = git -C $Repo -c core.quotepath=false ls-files --cached --others --exclude-standard
    foreach ($relativeRaw in $GitFiles) {
        $relative = $relativeRaw.Trim('"')
        $source = Join-Path $Repo $relative
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            $target = Join-Path $Stage $relative
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
            Copy-Item -LiteralPath $source -Destination $target -Force
        }
    }
    if (Test-Path -LiteralPath $OutPath) { Remove-Item -LiteralPath $OutPath -Force }
    Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $OutPath
    Get-FileHash -LiteralPath $OutPath -Algorithm SHA256 | Format-List
}
finally {
    if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
}
