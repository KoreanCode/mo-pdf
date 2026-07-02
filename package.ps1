$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$AppName = "O'range PDF Blur"
$ExeName = "OrangePdfBlur"
$BuildRoot = Join-Path $Root ".windows-build"
$BuildVenv = Join-Path $BuildRoot "build-venv"
$PyInstallerDist = Join-Path $BuildRoot "pyinstaller-dist"
$PyInstallerWork = Join-Path $BuildRoot "pyinstaller-work"
$Dist = Join-Path $Root "dist"
$PackageRoot = Join-Path $Dist "pdf-region-blur-app-windows"
$WindowsRoot = Join-Path $PackageRoot "Windows"
$ZipPath = Join-Path $Dist "O-range-PDF-Blur-Windows.zip"
$IconPng = Join-Path $Root "static\simbol_2.png"
$IconIco = Join-Path $BuildRoot "AppIcon.ico"
$TemplatesData = "$(Join-Path $Root 'templates');templates"
$StaticData = "$(Join-Path $Root 'static');static"
$LauncherPath = Join-Path $Root "launcher.py"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string] $FilePath,
        [Parameter(Mandatory = $true)][string[]] $Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath failed with exit code $LASTEXITCODE"
    }
}

function Find-BuildPython {
    $Candidates = @(
        @{ FilePath = "py"; Arguments = @("-3") },
        @{ FilePath = "python"; Arguments = @() },
        @{ FilePath = "python3"; Arguments = @() }
    )

    foreach ($Candidate in $Candidates) {
        $Command = Get-Command $Candidate.FilePath -ErrorAction SilentlyContinue
        if (-not $Command) {
            continue
        }

        $CheckArgs = $Candidate.Arguments + @(
            "-c",
            "import sys, tkinter, venv; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        )
        & $Candidate.FilePath @CheckArgs *> $null
        if ($LASTEXITCODE -eq 0) {
            return $Candidate
        }
    }

    throw "Build requires Python 3.10+ with tkinter and venv. Install Python from python.org, then run this again."
}

function Invoke-SourcePython {
    param([Parameter(Mandatory = $true)][string[]] $Arguments)

    Invoke-Checked -FilePath $BuildPythonCommand.FilePath -Arguments ($BuildPythonCommand.Arguments + $Arguments)
}

if (Test-Path $Dist) {
    Remove-Item -LiteralPath $Dist -Recurse -Force
}
if (Test-Path $BuildRoot) {
    Remove-Item -LiteralPath $BuildRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $PackageRoot -Force | Out-Null
New-Item -ItemType Directory -Path $WindowsRoot -Force | Out-Null
New-Item -ItemType Directory -Path $BuildRoot -Force | Out-Null

if (-not (Test-Path $IconPng)) {
    throw "Icon source was not found: $IconPng"
}

$BuildPythonCommand = Find-BuildPython
Invoke-SourcePython -Arguments @("-m", "venv", $BuildVenv)
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"

Invoke-Checked -FilePath $BuildPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked -FilePath $BuildPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt", "pyinstaller")

$IconScript = @'
from PIL import Image
import sys

source, destination = sys.argv[1], sys.argv[2]
image = Image.open(source).convert("RGBA")
image.save(destination, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
'@
Invoke-Checked -FilePath $BuildPython -Arguments @("-c", $IconScript, $IconPng, $IconIco)

Invoke-Checked -FilePath $BuildPython -Arguments @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", $ExeName,
    "--icon", $IconIco,
    "--distpath", $PyInstallerDist,
    "--workpath", $PyInstallerWork,
    "--specpath", $BuildRoot,
    "--add-data", $TemplatesData,
    "--add-data", $StaticData,
    "--hidden-import", "fitz",
    "--hidden-import", "PIL._tkinter_finder",
    "--collect-all", "fitz",
    $LauncherPath
)

$PyInstallerOutput = Join-Path $PyInstallerDist $ExeName
if (-not (Test-Path $PyInstallerOutput)) {
    throw "PyInstaller output was not found: $PyInstallerOutput"
}

Get-ChildItem -LiteralPath $PyInstallerOutput -Force | Copy-Item -Destination $WindowsRoot -Recurse -Force

$WindowsItems = @(
    "launcher_windows.bat",
    "start_windows.vbs",
    "stop_windows.bat",
    "stop_windows.vbs"
)

foreach ($Item in $WindowsItems) {
    $Source = Join-Path $Root $Item
    Copy-Item -LiteralPath $Source -Destination (Join-Path $WindowsRoot $Item)
}

@"
O'range PDF Blur 사용법

1. Windows 폴더에서 OrangePdfBlur.exe를 실행합니다.
2. 런처에서 [서버 실행]을 누릅니다.
3. [접속하기]를 눌러 브라우저를 엽니다.
4. 다 사용하면 [서버 종료]를 누릅니다.

Python을 따로 설치할 필요가 없습니다.
서버는 내 PC에서만 실행됩니다.
"@ | Set-Content -LiteralPath (Join-Path $PackageRoot "README.txt") -Encoding UTF8

Compress-Archive -Path (Join-Path $PackageRoot "*") -DestinationPath $ZipPath -Force
Write-Host "Created $ZipPath"
