param(
    [string]$Version = "2.1.2",
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"
$repositoryRoot = $PSScriptRoot
$temporaryBaseDirectory = Join-Path $env:LOCALAPPDATA "Temp"
$temporaryBuildDirectory = Join-Path $temporaryBaseDirectory ("organizer-build-" + [guid]::NewGuid())
$buildPython = Join-Path $temporaryBuildDirectory "venv\Scripts\python.exe"
$smokeInstallDirectory = Join-Path $temporaryBuildDirectory "installed"
$smokeAppDataDirectory = Join-Path $temporaryBuildDirectory "AppData"
$resourceDirectory = Join-Path $repositoryRoot "resources"
$iconPath = Join-Path $resourceDirectory "broom.ico"
$mainScript = Join-Path $repositoryRoot "source\main.py"
$originalAppData = $env:APPDATA
$installerWasRun = $false

function Invoke-CheckedCommand {
    param(
        [string]$Executable,
        [string[]]$Arguments
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Executable $Arguments"
    }
}

function Find-InnoSetupCompiler {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $knownLocations = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($location in $knownLocations) {
        if ($location -and (Test-Path -LiteralPath $location)) {
            return $location
        }
    }

    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php."
}

function Remove-TemporaryPath {
    param([string]$Path)

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        if (-not (Test-Path -LiteralPath $Path)) {
            return
        }

        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        } catch {
            if ($attempt -eq 5) {
                throw "Could not remove temporary path after $attempt attempts: $Path. $($_.Exception.Message)"
            }
            Start-Sleep -Seconds 1
        }
    }
}

try {
    Set-Location $repositoryRoot

    if ($PythonPath) {
        if (-not (Test-Path -LiteralPath $PythonPath)) {
            throw "Python executable not found: $PythonPath"
        }
        $pythonExecutable = $PythonPath
        $pythonArguments = @()
    } else {
        $pythonLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
        if (-not $pythonLauncher) {
            throw "The Python launcher was not found. Install Python 3.12 and enable the py launcher."
        }
        $pythonExecutable = $pythonLauncher.Source
        $pythonArguments = @("-3.12")
    }
    Invoke-CheckedCommand $pythonExecutable ($pythonArguments + @("--version"))
    Invoke-CheckedCommand $pythonExecutable (
        $pythonArguments + @(
            "-c",
            "import sys; assert sys.version_info[:2] == (3, 12), sys.version"
        )
    )

    $compiler = Find-InnoSetupCompiler
    New-Item -ItemType Directory -Path $temporaryBuildDirectory | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $repositoryRoot "Output") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $repositoryRoot "dist") -Force | Out-Null
    $venvArguments = $pythonArguments + @(
        "-m", "venv", (Join-Path $temporaryBuildDirectory "venv")
    )
    Invoke-CheckedCommand $pythonExecutable $venvArguments
    Invoke-CheckedCommand $buildPython @(
        "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt"
    )
    Invoke-CheckedCommand $buildPython @(
        "-m", "unittest", "discover", "-s", "tests", "-v"
    )
    Invoke-CheckedCommand $buildPython @(
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "main",
        "--log-level", "WARN",
        "--specpath", $temporaryBuildDirectory,
        "--workpath", (Join-Path $temporaryBuildDirectory "pyinstaller-build"),
        "--distpath", (Join-Path $repositoryRoot "dist"),
        "--icon", $iconPath,
        "--add-data", "$resourceDirectory;resources",
        $mainScript
    )
    Invoke-CheckedCommand $compiler @(
        "/Qp",
        "/DMyAppVersion=$Version",
        "installer_script.iss"
    )

    $installerPath = Join-Path $repositoryRoot "Output\download-organizer-setup.exe"
    if (-not (Test-Path -LiteralPath $installerPath)) {
        throw "Inno Setup completed without producing $installerPath."
    }

    New-Item -ItemType Directory -Path $smokeAppDataDirectory | Out-Null
    $env:APPDATA = $smokeAppDataDirectory
    $installerWasRun = $true
    Invoke-CheckedCommand $installerPath @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/DIR=$smokeInstallDirectory"
    )

    $installedExecutable = Join-Path $smokeInstallDirectory "main.exe"
    $installedLegacyConfig = Join-Path $smokeInstallDirectory "config.yaml"
    if (-not (Test-Path -LiteralPath $installedLegacyConfig)) {
        $installedItems = @(Get-ChildItem -LiteralPath $smokeInstallDirectory -Name -ErrorAction SilentlyContinue)
        throw "Installer did not include the legacy configuration seed: $installedLegacyConfig. Installed files: $($installedItems -join ', ')."
    }
    @"
interval: 19
rules: []
"@ | Set-Content -LiteralPath $installedLegacyConfig -Encoding ascii
    Invoke-CheckedCommand $installedExecutable @("--check-config")

    $migratedConfig = Join-Path $smokeAppDataDirectory "Organizer\config.yaml"
    if (
        -not (Test-Path -LiteralPath $migratedConfig) -or
        (Get-Content -LiteralPath $migratedConfig -Raw) -notmatch "interval:\s*19"
    ) {
        throw "Packaged app did not migrate the installed legacy configuration."
    }
    @"
interval: 17
rules: []
"@ | Set-Content -LiteralPath $migratedConfig -Encoding ascii
    Invoke-CheckedCommand $installedExecutable @("--check-config")
    if ((Get-Content -LiteralPath $migratedConfig -Raw) -notmatch "interval:\s*17") {
        throw "The packaged app overwrote the existing per-user configuration."
    }

    Write-Host "Installer created and install/configuration smoke test passed: $installerPath"
}
finally {
    if ($installerWasRun) {
        $uninstaller = Join-Path $smokeInstallDirectory "unins000.exe"
        if (Test-Path -LiteralPath $uninstaller) {
            $uninstallProcess = Start-Process -FilePath $uninstaller -WorkingDirectory $smokeInstallDirectory -ArgumentList @(
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART"
            ) -Wait -PassThru
            if ($uninstallProcess.ExitCode -ne 0) {
                Write-Warning "Temporary installer uninstall returned exit code $($uninstallProcess.ExitCode); removing only its isolated smoke-test files and registration."
            }
        }

        $uninstallRegistryRoot = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall"
        if (Test-Path -LiteralPath $uninstallRegistryRoot) {
            foreach ($entry in Get-ChildItem -LiteralPath $uninstallRegistryRoot) {
                $registration = Get-ItemProperty -LiteralPath $entry.PSPath -ErrorAction SilentlyContinue
                if (
                    $registration.UninstallString -and
                    $registration.UninstallString.IndexOf(
                        $smokeInstallDirectory,
                        [System.StringComparison]::OrdinalIgnoreCase
                    ) -ge 0
                ) {
                    Remove-Item -LiteralPath $entry.PSPath -Recurse -Force
                }
            }
        }

        if (Test-Path -LiteralPath $smokeInstallDirectory) {
            Remove-TemporaryPath $smokeInstallDirectory
        }
    }
    $env:APPDATA = $originalAppData
    if (Test-Path -LiteralPath $temporaryBuildDirectory) {
        Remove-TemporaryPath $temporaryBuildDirectory
    }
}
