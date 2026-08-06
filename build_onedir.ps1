# Build a one-dir executable for the Modeling app using PyInstaller
# Usage (PowerShell):
#   & "venv\Scripts\Activate.ps1"; .\build_onedir.ps1

param(
    [string]$venvPath = "venv",
    [string]$entry = "run.py",
    [string]$distDir = "dist",
    [string]$workDir = "build"
)

# Ensure venv activation was attempted by the caller; this script uses the active Python.
Write-Host "Building one-dir executable for $entry"

# Install PyInstaller in the venv if missing
& "$venvPath\Scripts\pip.exe" install --upgrade pyinstaller | Out-Null

# Run pyinstaller in one-dir mode (default) with necessary options for PyQt5
# --noconfirm: overwrite output dir
# --clean: clean PyInstaller cache and temp files
# --distpath: output folder for executable
# --workpath: temporary build folder
# --add-data: include any non-Python resources (example shown commented)

if (Test-Path "pyinstaller_modeling.spec") {
    Write-Host 'Found pyinstaller_modeling.spec - running PyInstaller with the spec (ensures custom hooks are used).'
    # No --clean here: OneDrive can hold locks on the build cache dir, which
    # makes PyInstaller's pre-build rmtree fail with WinError 5.
    & "$venvPath\Scripts\pyinstaller.exe" --noconfirm --distpath $distDir --workpath $workDir "pyinstaller_modeling.spec"
} else {
    $pyinstallerCmd = @(
        "-y",
        "--noconfirm",
        "--clean",
        "--distpath", $distDir,
        "--workpath", $workDir,
        "--windowed",
        $entry
    )
    Write-Host "Running PyInstaller..."
    & "$venvPath\Scripts\pyinstaller.exe" @pyinstallerCmd
}

if ($LASTEXITCODE -eq 0) {
    # -LeafBase is PowerShell 6+; use basename via GetFileNameWithoutExtension for PS 5.1.
    $entryName = [System.IO.Path]::GetFileNameWithoutExtension($entry)
    Write-Host ("Build complete. One-dir output is in: {0}\{1}" -f $distDir, $entryName)
} else {
    Write-Error ("PyInstaller failed with exit code {0}" -f $LASTEXITCODE)
}
