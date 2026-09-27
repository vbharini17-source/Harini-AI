$ErrorActionPreference = "Stop"

$pythonCandidates = @()
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher -and $launcher.Source -notlike "*WindowsApps*") {
    $pythonCandidates += [pscustomobject]@{
        Executable = $launcher.Source
        PrefixArgs = @("-3")
    }
}

foreach ($root in @("$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles\Python")) {
    Get-ChildItem -Path $root -Directory -Filter "Python*" -ErrorAction SilentlyContinue |
        ForEach-Object {
            $candidate = Join-Path $_.FullName "python.exe"
            if (Test-Path $candidate) {
                $pythonCandidates += [pscustomobject]@{
                    Executable = $candidate
                    PrefixArgs = @()
                }
            }
        }
}

$pathPython = Get-Command python -ErrorAction SilentlyContinue
if ($pathPython -and $pathPython.Source -notlike "*WindowsApps*") {
    $pythonCandidates += [pscustomobject]@{
        Executable = $pathPython.Source
        PrefixArgs = @()
    }
}

$pythonExe = $null
$pythonArgs = @()
foreach ($candidate in $pythonCandidates) {
    $candidateVersion = & $candidate.Executable @($candidate.PrefixArgs) --version 2>&1
    if ($candidateVersion -match "^Python (?<Version>\d+\.\d+)") {
        if ([version]$Matches.Version -ge [version]"3.10") {
            $pythonExe = $candidate.Executable
            $pythonArgs = $candidate.PrefixArgs
            $versionText = $candidateVersion
            break
        }
    }
}

if (-not $pythonExe) {
    throw "Python 3.10+ is required. Install it from https://www.python.org/downloads/ and rerun this script."
}

Write-Host "Using $versionText" -ForegroundColor Green
if (-not (Test-Path ".venv")) {
    & $pythonExe @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
}

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $venvPython -m pytest
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

$gitCommand = Get-Command git -ErrorAction SilentlyContinue
$gitExe = if ($gitCommand -and $gitCommand.Source -notlike "*WindowsApps*") {
    $gitCommand.Source
} else {
    @("$env:ProgramFiles\Git\cmd\git.exe", "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe") |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1
}

if (-not $gitExe) {
    throw "Git is required. Install Git for Windows, then rerun .\setup.ps1."
}

if (-not (Test-Path ".git")) {
    & $gitExe init
    if ($LASTEXITCODE -ne 0) { throw "git init failed." }
    & $gitExe branch -M main
    if ($LASTEXITCODE -ne 0) { throw "Could not set the initial branch to main." }
}

& $gitExe add .
if ($LASTEXITCODE -ne 0) { throw "git add failed." }

Write-Host "Setup complete. Review staged files, then add a remote and push when ready." -ForegroundColor Green