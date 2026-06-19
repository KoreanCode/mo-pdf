$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $Root "dist"
$PackageRoot = Join-Path $Dist "pdf-region-blur-app"
$WindowsRoot = Join-Path $PackageRoot "Windows"
$MacRoot = Join-Path $PackageRoot "macOS"
$ZipPath = Join-Path $Dist "pdf-region-blur-app.zip"

if (Test-Path $Dist) {
    Remove-Item -LiteralPath $Dist -Recurse -Force
}

New-Item -ItemType Directory -Path $WindowsRoot | Out-Null
New-Item -ItemType Directory -Path $MacRoot | Out-Null

$CommonRuntimeItems = @(
    "app.py",
    "launcher.py",
    "pdf_blur.py",
    "requirements.txt",
    "templates",
    "static"
)

foreach ($Item in $CommonRuntimeItems) {
    $Source = Join-Path $Root $Item
    Copy-Item -LiteralPath $Source -Destination (Join-Path $WindowsRoot $Item) -Recurse
    Copy-Item -LiteralPath $Source -Destination (Join-Path $MacRoot $Item) -Recurse
}

$TextDocs = @(
    @{ Source = "README.md"; Destination = "README.txt" },
    @{ Source = "USER_GUIDE_KO.md"; Destination = "USER_GUIDE_KO.txt" }
)

foreach ($Doc in $TextDocs) {
    $Source = Join-Path $Root $Doc.Source
    $Destination = Join-Path $PackageRoot $Doc.Destination
    Get-Content -LiteralPath $Source -Raw -Encoding UTF8 | Set-Content -LiteralPath $Destination -Encoding UTF8
}

$DocsSource = Join-Path $Root "docs"
$DocsDestination = Join-Path $PackageRoot "docs"
New-Item -ItemType Directory -Path $DocsDestination | Out-Null

Get-ChildItem -LiteralPath $DocsSource -Recurse -File | ForEach-Object {
    $RelativePath = $_.FullName.Substring($DocsSource.Length).TrimStart("\", "/")
    $DestinationRelativePath = if ($_.Extension -eq ".md") {
        [System.IO.Path]::ChangeExtension($RelativePath, ".txt")
    } else {
        $RelativePath
    }
    $Destination = Join-Path $DocsDestination $DestinationRelativePath
    $DestinationParent = Split-Path -Parent $Destination
    if ($DestinationParent -and -not (Test-Path $DestinationParent)) {
        New-Item -ItemType Directory -Path $DestinationParent | Out-Null
    }

    if ($_.Extension -eq ".md") {
        Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | Set-Content -LiteralPath $Destination -Encoding UTF8
    } else {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination
    }
}

$WindowsItems = @(
    "launcher_windows.bat",
    "run_windows.bat",
    "start_windows.vbs",
    "stop_windows.bat",
    "stop_windows.vbs"
)

foreach ($Item in $WindowsItems) {
    $Source = Join-Path $Root $Item
    Copy-Item -LiteralPath $Source -Destination (Join-Path $WindowsRoot $Item)
}

$MacItems = @(
    "launcher_mac.command",
    "build_mac_dmg.command",
    "run_mac.command",
    "start_mac.command",
    "stop_mac.command"
)

foreach ($Item in $MacItems) {
    $Source = Join-Path $Root $Item
    Copy-Item -LiteralPath $Source -Destination (Join-Path $MacRoot $Item)
}

Compress-Archive -Path (Join-Path $PackageRoot "*") -DestinationPath $ZipPath -Force
Write-Host "Created $ZipPath"
